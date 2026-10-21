# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *
import typing
from dataclasses import dataclass

# Depolama (Storage) için özel bir veri yapısı oluşturuyoruz
@allow_storage
@dataclass
class AuditResult:
    risk_score: u8
    is_safe: bool
    analysis: str

class TokenAuditor(gl.Contract):
    # Proje URL'lerini ve denetim sonuçlarını tutacağımız eşleme tablosu
    audits: TreeMap[str, AuditResult]

    def __init__(self):
        # Başlangıçta boş bir tablo oluşturuyoruz
        pass

    @gl.public.write
    def audit_project(self, project_url: str) -> None:
        # Eğer proje daha önce denetlendiyse tekrar işlem yapma
        if project_url in self.audits:
            return

        def leader_fn():
            # URL'den web içeriğini çekiyoruz
            web_data = gl.nondet.web.render(project_url, mode="text")
            
            prompt = f"""
            Analyze this Web3 project website for rug-pull risks, missing tokenomics, or red flags.
            Website Content: {web_data[:3000]}
            
            Return ONLY a valid JSON with these keys:
            - "risk_score": integer from 0 (safest) to 100 (highest risk)
            - "is_safe": boolean (true if risk_score is under 50)
            - "analysis": "A short 2-sentence reasoning"
            """
            # LLM'i JSON formatında yanıt vermeye zorluyoruz
            res = gl.nondet.exec_prompt(prompt, response_format="json")
            return res 

        def validator_fn(leader_result) -> bool:
            # Lider hata verdiyse reddet
            if not isinstance(leader_result, gl.vm.Return):
                return False
            
            leader_data = leader_result.calldata
            validator_data = leader_fn() # Doğrulayıcı olarak veriyi kendimiz de çekip analiz ediyoruz

            # 1. Kural: Projenin "Güvenli" (is_safe) kararı kesinlikle eşleşmeli
            if leader_data.get("is_safe") != validator_data.get("is_safe"):
                return False
            
            # 2. Kural: Risk skoru LLM'den LLM'e değişebilir, maksimum 15 puanlık sapmaya (tolerans) izin veriyoruz
            leader_score = int(leader_data.get("risk_score", 100))
            validator_score = int(validator_data.get("risk_score", 100))
            
            score_diff = abs(leader_score - validator_score)
            return score_diff <= 15

        # Özel doğrulamayı çalıştırıyoruz
        result = gl.vm.run_nondet_unsafe(leader_fn, validator_fn)

        # Çıkan ve onaylanan sonucu blockchain üzerindeki state'e (duruma) kaydediyoruz
        self.audits[project_url] = AuditResult(
            risk_score=u8(result["risk_score"]),
            is_safe=result["is_safe"],
            analysis=result["analysis"]
        )

    @gl.public.view
    def get_audit(self, project_url: str) -> TreeMap[str, typing.Any]:
        # İstenen projenin denetim raporunu okuma metodu
        return self.audits.get(project_url, AuditResult(u8(0), False, "Not audited yet"))