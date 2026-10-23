# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *
import typing
from dataclasses import dataclass

@allow_storage
@dataclass
class AuditResult:
    risk_score: u8
    is_safe: bool
    analysis: str

class TokenAuditor(gl.Contract):
    audits: TreeMap[str, AuditResult]

    def __init__(self):
        pass

    @gl.public.write
    def audit_project(self, project_url: str) -> None:
        if project_url in self.audits:
            return

        def leader_fn():
            web_data = gl.nondet.web.render(project_url, mode="text")
            
            prompt = f"""
            Analyze this Web3 project website for rug-pull risks, missing tokenomics, or red flags.
            Website Content: {web_data[:3000]}
            
            Return ONLY a valid JSON with these keys:
            - "risk_score": integer from 0 (safest) to 100 (highest risk)
            - "is_safe": boolean (true if risk_score is under 50)
            - "analysis": "A short 2-sentence reasoning"
            """
            return gl.nondet.exec_prompt(prompt, response_format="json")

        def validator_fn(leader_result) -> bool:
            if not isinstance(leader_result, gl.vm.Return):
                return False
            
            leader_data = leader_result.calldata
            leader_score = int(leader_data.get("risk_score", 100))
            
            # KESİN KURALLAR (INVARIANTS):
            # 1. Skor 0-100 arasında olmalı.
            if not (0 <= leader_score <= 100):
                return False
                
            # 2. is_safe kesinlikle skorun 50'nin altında olması durumuna eşit olmalı.
            if bool(leader_data.get("is_safe")) != (leader_score < 50):
                return False

            validator_data = leader_fn()
            
            if leader_data.get("is_safe") != validator_data.get("is_safe"):
                return False
                
            validator_score = int(validator_data.get("risk_score", 100))
            return abs(leader_score - validator_score) <= 15

        result = gl.vm.run_nondet_unsafe(leader_fn, validator_fn)

        self.audits[project_url] = AuditResult(
            risk_score=u8(result["risk_score"]),
            is_safe=result["is_safe"],
            analysis=result["analysis"]
        )

    @gl.public.view
    def get_audit(self, project_url: str) -> TreeMap[str, typing.Any]:
        return self.audits.get(project_url, AuditResult(u8(0), False, "Not audited yet"))
