from dataclasses import dataclass

from app.adapters.email import ConfiguredEmailProvider, RuntimeEmailConfig
from app.adapters.email_jobs import FileEmailJobRepository, SupabaseEmailJobRepository
from app.adapters.kalshi import KalshiHttpAdapter
from app.adapters.linear import LinearTaskTrackerAdapter
from app.adapters.memory import MentisMemoryAdapter
from app.adapters.open_claw import OpenClawLLMAdapter
from app.adapters.pilot_web import PilotWebAdapter
from app.adapters.trading_audit import SupabaseTradeAuditRepository, SupabaseTradingExposureRepository
from app.adapters.zernio_adapter import ZernioAdapter
from app.domain.trading_policies import ConfigurableRiskPolicy
from app.runtime.rate_limit import InMemoryRateLimiter
from app.runtime.tracing import RuntimeTracer
from app.use_cases.coder_web_graph import CoderWebGraph
from app.use_cases.email_workflow import EmailWorkflow
from app.use_cases.marketing_graph import MarketingGraph
from app.use_cases.model_status import ModelStatusService
from app.use_cases.orchestrator_workflow import OrchestratorWorkflow
from app.use_cases.picture_graph import PictureGraph
from app.use_cases.trading_workflow import TradingWorkflow
from app.use_cases.writer_workflow import WriterWorkflow


@dataclass
class AssistantRuntimeContainer:
    trading_workflow: TradingWorkflow
    marketing_workflow: MarketingGraph
    writer_workflow: WriterWorkflow
    email_workflow: EmailWorkflow
    picture_workflow: PictureGraph
    coder_web_workflow: CoderWebGraph
    orchestrator_workflow: OrchestratorWorkflow
    model_status_service: ModelStatusService
    rate_limiter: InMemoryRateLimiter
    tracer: RuntimeTracer


def build_runtime_container() -> AssistantRuntimeContainer:
    llm_port = OpenClawLLMAdapter()
    memory_port = MentisMemoryAdapter()
    email_config = RuntimeEmailConfig()
    return AssistantRuntimeContainer(
        trading_workflow=TradingWorkflow(
            trading_port=KalshiHttpAdapter(),
            llm_port=llm_port,
            memory_port=memory_port,
            risk_policy=ConfigurableRiskPolicy(exposure_repository=SupabaseTradingExposureRepository()),
            audit_repository=SupabaseTradeAuditRepository(),
        ),
        marketing_workflow=MarketingGraph(llm=llm_port, memory=memory_port, marketing=ZernioAdapter()),
        writer_workflow=WriterWorkflow(llm_port=llm_port, memory_port=memory_port),
        email_workflow=EmailWorkflow(
            email_provider=ConfiguredEmailProvider(email_config),
            email_config=email_config,
            email_jobs=_email_job_repository(),
            llm=llm_port,
        ),
        picture_workflow=PictureGraph(llm=llm_port, memory=memory_port),
        coder_web_workflow=CoderWebGraph(
            llm=llm_port,
            memory=memory_port,
            coder_web=PilotWebAdapter(),
            task_tracker=LinearTaskTrackerAdapter(),
        ),
        orchestrator_workflow=OrchestratorWorkflow(llm_port=llm_port),
        model_status_service=ModelStatusService(llm=llm_port),
        rate_limiter=InMemoryRateLimiter(),
        tracer=RuntimeTracer(),
    )


def _email_job_repository():
    requested = __import__("os").getenv("EMAIL_JOB_REPOSITORY", "auto").lower()
    supabase_repo = SupabaseEmailJobRepository()
    if requested == "file":
        return FileEmailJobRepository()
    if requested == "supabase" or (requested == "auto" and supabase_repo.configured):
        return supabase_repo
    return FileEmailJobRepository()
