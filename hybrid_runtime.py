from dataclasses import dataclass
from llm_runtime import LLMProvider, LLMResponse, LLMRuntime
from afe_vantage import AFE, Task, Verdict

@dataclass
class HybridResponse:
    primary: LLMResponse
    secondary: LLMResponse
    final_text: str
    agreement: bool
    verifier: str
    audit: list[str]

class HybridLLMRuntime:
    """Two-provider LLM path with the same Vantage gate and deterministic disagreement check."""
    def __init__(self, primary: LLMProvider, secondary: LLMProvider):
        self.primary=LLMRuntime(AFE(), primary)
        self.secondary=LLMRuntime(AFE(), secondary)

    def run(self, task: Task) -> HybridResponse:
        p=self.primary.run(task)
        audit=list(p.audit)
        if p.blocked:
            audit.append("HYBRID: primary blocked; secondary not invoked")
            return HybridResponse(p, LLMResponse("", "none", "none", True, []), "", False, "vantage", audit)

        s=self.secondary.run(task)
        audit += [f"HYBRID: secondary provider={s.provider} model={s.model}"]
        if s.blocked:
            audit.append("HYBRID: secondary blocked")
            return HybridResponse(p,s,p.text,False,"vantage",audit)

        agreement=(p.text == s.text)
        audit.append(f"HYBRID: agreement={agreement}")
        if not agreement:
            audit.append("HYBRID: contradiction detected; human approval required")
            return HybridResponse(p,s,"",False,"contradiction-gate",audit)

        audit.append("HYBRID: independent providers agree; output released")
        return HybridResponse(p,s,p.text,True,"dual-provider",audit)
