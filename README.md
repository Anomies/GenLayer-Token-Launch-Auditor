Token Launch Auditor - GenLayer Intelligent Contract
Overview
Token Launch Auditor is a decentralized, AI-driven Intelligent Contract built on GenLayer. It autonomously evaluates new Web3 project websites for potential rug-pull risks, missing tokenomics, and red flags.

Unlike traditional deterministic smart contracts that require off-chain oracles, this contract natively fetches client-side rendered web content using GenLayer's gl.nondet.web.render(..., mode="text") and uses LLMs to dynamically assess project safety.

Why This Matters (Use Case)
In the fast-paced Web3 ecosystem, investors and automated trading bots often lack the time to thoroughly vet every new token launch. This contract provides a decentralized "Trust Score" primitive. Other smart contracts, trading bots, or decentralized launchpads can query this contract's state before interacting with a newly launched project, significantly reducing the risk of engaging with malicious actors.

How Consensus & The Equivalence Principle is Used 
This contract avoids the pitfall of "blindly trusting the leader" by utilizing a custom validator pattern via gl.vm.run_nondet_unsafe. Because LLM outputs are inherently non-deterministic, generating strict byte-for-byte matches across nodes is impossible for qualitative analysis.

   To solve this, the contract implements a Tolerant Gating Mechanism:
   1. The Leader Node fetches the website's raw text, feeds it to the LLM, and proposes a structured JSON outcome containing a risk_score (0-100), an is_safe boolean, and a short analysis.

   2. Validator Nodes independently fetch the same website and run their own LLM analysis.

   3. **Consensus Rules & Invariants:**
   * **Strict Invariant Enforcement:** The validator strictly enforces the 0–100 score range and ensures the invariant that `is_safe` is `true` *if and only if* the accepted `risk_score` is strictly below 50. If a          leader proposes contradictory data (e.g., a score of 60 marked as safe), the validator instantly rejects the proposal to guarantee one consistent safety outcome.
   * **Strict Boolean Matching:** Both the leader and the validator must independently reach the exact same `is_safe` conclusion. 
   * **Numeric Tolerance:** Recognizing that LLM scoring is subjective, the validators allow a maximum `risk_score` divergence of ±15 points, provided all the strict invariants and boolean matches mentioned above hold      true.

Contract Usage
1. *audit_project(project_url: str)*
Triggers the AI audit process. The contract fetches the provided URL, evaluates it, reaches network consensus based on the defined tolerance, and persists the result to the blockchain state.

2. *get_audit(project_url: str)*
A view method that returns the current consensus-backed audit result for a given project URL, including the risk score, safety status, and the leader's brief reasoning.

Technical Considerations & Best Practices Applied
- Dynamic Web Rendering: Uses *mode="text"* to ensure modern JavaScript-heavy (React/Next.js) Web3 websites are fully rendered before text extraction, preventing false positives (e.g., scoring an empty HTML shell).
- Structured State: Utilizes GenLayer's TreeMap and @allow_storage dataclasses for highly efficient and type-safe state management.
- Idempotency Check: Prevents redundant processing and unnecessary gas/fee consumption by instantly returning if a project URL has already been audited.
