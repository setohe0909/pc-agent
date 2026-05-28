import { useEffect, useMemo, useRef, useState } from "react";
import {
  Bot,
  BrainCircuit,
  Camera,
  CheckCircle2,
  Cpu,
  Keyboard,
  Mail,
  Maximize2,
  Megaphone,
  Mic,
  MicOff,
  Minimize2,
  PenTool,
  Radio,
  Send,
  ShieldCheck,
  Sparkles,
  Volume2,
  VolumeX,
  Zap,
} from "lucide-react";
import { submitAssistantRequest } from "@/lib/api";
import { Button } from "@/components/ui/button";

type AssistantAction = "chat" | "marketing" | "email" | "writer" | "picture" | "coder-web" | "model_status";
type MessageRole = "assistant" | "user" | "system";

type AssistantMessage = {
  id: string;
  role: MessageRole;
  text: string;
  time: string;
};

type AssistanceViewProps = {
  data: AssistanceDashboardData | null;
  adminToken: string;
};

const assistantName = "AURORA";

type AssistanceDashboardData = {
  status?: {
    services?: Array<{ name?: string; state?: string }>;
  } | null;
};

type AssistantResponse = {
  message?: string;
  detail?: string;
  reason?: string;
};

type SpeechRecognitionResultEventLike = {
  results?: {
    [index: number]: {
      [index: number]: {
        transcript?: string;
      };
    };
  };
};

type SpeechRecognitionLike = {
  lang: string;
  interimResults: boolean;
  continuous: boolean;
  onresult: ((event: SpeechRecognitionResultEventLike) => void) | null;
  onend: (() => void) | null;
  onerror: (() => void) | null;
  start: () => void;
  stop: () => void;
};

type SpeechRecognitionConstructor = new () => SpeechRecognitionLike;

type SpeechRecognitionWindow = Window & {
  SpeechRecognition?: SpeechRecognitionConstructor;
  webkitSpeechRecognition?: SpeechRecognitionConstructor;
};

const actionOptions: Array<{ value: AssistantAction; label: string; icon: typeof Bot; subCommand?: string }> = [
  { value: "chat", label: "General", icon: Sparkles },
  { value: "marketing", label: "Marketing", icon: Megaphone, subCommand: "chat" },
  { value: "email", label: "Email", icon: Mail, subCommand: "status" },
  { value: "writer", label: "Redactor", icon: PenTool },
  { value: "picture", label: "Imagen", icon: Camera },
  { value: "coder-web", label: "Coder", icon: Keyboard },
  { value: "model_status", label: "Modelos", icon: Cpu },
];

const quickPrompts = [
  "Dame el estado de los agentes conectados.",
  "Revisa la configuracion de Discord y dime que falta.",
  "Prepara una accion de marketing para leads recientes.",
  "Consulta el estado del agente de email.",
];

function currentTime() {
  return new Intl.DateTimeFormat("es-CO", { hour: "2-digit", minute: "2-digit" }).format(new Date());
}

function detectAction(prompt: string, fallback: AssistantAction): AssistantAction {
  const text = prompt.toLowerCase();
  if (text.includes("marketing") || text.includes("campana") || text.includes("leads")) return "marketing";
  if (text.includes("email") || text.includes("correo")) return "email";
  if (text.includes("redact") || text.includes("articulo") || text.includes("writer")) return "writer";
  if (text.includes("imagen") || text.includes("foto") || text.includes("picture")) return "picture";
  if (text.includes("codigo") || text.includes("web") || text.includes("coder")) return "coder-web";
  if (text.includes("modelo") || text.includes("proveedor")) return "model_status";
  return fallback;
}

function responseText(response: AssistantResponse) {
  return response?.message || response?.detail || response?.reason || "Solicitud procesada sin mensaje de texto.";
}

function serviceState(data: AssistanceDashboardData | null, name: string) {
  return data?.status?.services?.find((service) => service.name === name)?.state || "unknown";
}

function voiceScore(voice: SpeechSynthesisVoice) {
  const name = voice.name.toLowerCase();
  const lang = voice.lang.toLowerCase();
  let score = lang.startsWith("es") ? 20 : 0;
  if (lang.includes("419") || lang.includes("mx") || lang.includes("co") || lang.includes("us")) score += 8;
  if (name.includes("premium") || name.includes("enhanced") || name.includes("neural")) score += 14;
  if (name.includes("google") || name.includes("microsoft") || name.includes("apple")) score += 8;
  if (name.includes("paulina") || name.includes("jorge") || name.includes("mónica") || name.includes("monica")) score += 5;
  return score;
}

function bestSpanishVoice(voices: SpeechSynthesisVoice[]) {
  return [...voices].sort((left, right) => voiceScore(right) - voiceScore(left))[0];
}

function speechChunks(text: string) {
  const clean = text
    .replace(/[`*_#>~]/g, "")
    .replace(/\s+/g, " ")
    .trim();
  const sentences = clean.match(/[^.!?;:]+[.!?;:]?/g) || [clean];
  const chunks: string[] = [];
  let current = "";
  for (const sentence of sentences) {
    const next = `${current} ${sentence}`.trim();
    if (next.length > 220 && current) {
      chunks.push(current);
      current = sentence.trim();
    } else {
      current = next;
    }
  }
  if (current) chunks.push(current);
  return chunks;
}

export function AssistanceView({ data, adminToken }: AssistanceViewProps) {
  const [prompt, setPrompt] = useState("");
  const [activeAction, setActiveAction] = useState<AssistantAction>("chat");
  const [messages, setMessages] = useState<AssistantMessage[]>([
    {
      id: "welcome",
      role: "assistant",
      text: `Soy ${assistantName}. Canal administrativo listo para coordinar agentes, Discord y runtime en español.`,
      time: currentTime(),
    },
  ]);
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(true);
  const [isSending, setIsSending] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([]);
  const [voiceName, setVoiceName] = useState("");
  const recognitionRef = useRef<SpeechRecognitionLike | null>(null);
  const logRef = useRef<HTMLDivElement | null>(null);

  const selectedVoice = useMemo(() => {
    return voices.find((voice) => voice.name === voiceName) || bestSpanishVoice(voices) || voices[0];
  }, [voiceName, voices]);

  const runtimeState = serviceState(data, "assistant-runtime");
  const discordState = serviceState(data, "discord-bot");
  const healthyServices = data?.status?.services?.filter((service) => service.state === "healthy").length || 0;
  const totalServices = data?.status?.services?.length || 0;

  useEffect(() => {
    const loadVoices = () => {
      const available = window.speechSynthesis?.getVoices?.() || [];
      setVoices(available);
      const spanish = bestSpanishVoice(available);
      if (!voiceName && spanish) setVoiceName(spanish.name);
    };
    loadVoices();
    window.speechSynthesis?.addEventListener("voiceschanged", loadVoices);
    return () => window.speechSynthesis?.removeEventListener("voiceschanged", loadVoices);
  }, [voiceName]);

  useEffect(() => {
    logRef.current?.scrollTo({ top: logRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    if (!isExpanded) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = previousOverflow;
    };
  }, [isExpanded]);

  const speak = (text: string) => {
    if (!isSpeaking || !window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    const chunks = speechChunks(text);
    const speakChunk = (index: number) => {
      const chunk = chunks[index];
      if (!chunk) return;
      const utterance = new SpeechSynthesisUtterance(chunk);
      utterance.lang = selectedVoice?.lang || "es-419";
      utterance.rate = 0.96;
      utterance.pitch = 0.84;
      utterance.volume = 0.98;
      if (selectedVoice) utterance.voice = selectedVoice;
      utterance.onend = () => speakChunk(index + 1);
      window.speechSynthesis.speak(utterance);
    };
    speakChunk(0);
  };

  const appendMessage = (role: MessageRole, text: string) => {
    setMessages((current) => [...current, { id: crypto.randomUUID(), role, text, time: currentTime() }]);
  };

  const submitPrompt = async (rawPrompt = prompt) => {
    const cleanPrompt = rawPrompt.trim();
    if (!cleanPrompt || isSending) return;
    if (!adminToken) {
      appendMessage("system", "Configura el Admin Token para enviar peticiones al runtime.");
      return;
    }
    const action = detectAction(cleanPrompt, activeAction);
    const option = actionOptions.find((item) => item.value === action);
    setActiveAction(action);
    setPrompt("");
    appendMessage("user", cleanPrompt);
    setIsSending(true);

    try {
      const response = await submitAssistantRequest({
        action_type: action,
        prompt: cleanPrompt,
        source: { platform: "admin", channel_id: "assistance-ui", user_id: "admin" },
        payload: {
          sub_command: option?.subCommand || "chat",
          agent: action === "model_status" ? "marketing" : action,
          interface: "assistance",
          language: "es",
        },
      }, adminToken);
      const answer = responseText(response);
      appendMessage("assistant", answer);
      speak(answer);
    } catch (error) {
      const message = error instanceof Error ? error.message : "error desconocido";
      appendMessage("system", `No pude completar la peticion: ${message}`);
    } finally {
      setIsSending(false);
    }
  };

  const toggleListening = () => {
    const speechWindow = window as SpeechRecognitionWindow;
    const SpeechRecognitionApi = speechWindow.SpeechRecognition || speechWindow.webkitSpeechRecognition;
    if (!SpeechRecognitionApi) {
      appendMessage("system", "Este navegador no expone reconocimiento de voz local.");
      return;
    }
    if (isListening) {
      recognitionRef.current?.stop();
      setIsListening(false);
      return;
    }
    const recognition = new SpeechRecognitionApi();
    recognition.lang = "es-CO";
    recognition.interimResults = false;
    recognition.continuous = false;
    recognition.onresult = (event) => {
      const transcript = event.results?.[0]?.[0]?.transcript || "";
      setPrompt(transcript);
      void submitPrompt(transcript);
    };
    recognition.onend = () => setIsListening(false);
    recognition.onerror = () => {
      appendMessage("system", "El dictado se detuvo antes de recibir audio claro.");
      setIsListening(false);
    };
    recognitionRef.current = recognition;
    recognition.start();
    setIsListening(true);
  };

  return (
    <div className={`assistance-shell ${isExpanded ? "assistance-shell-expanded fixed inset-0 z-50 h-[100dvh] rounded-none border-0" : "min-h-[calc(100vh-180px)] rounded-[8px] border"} overflow-hidden border-cyan-300/10 bg-[#050b10] text-cyan-50 shadow-[0_20px_80px_rgba(0,0,0,0.35)]`}>
      <div className="assistance-topbar flex flex-col gap-3 border-b border-cyan-300/10 px-4 py-4 md:flex-row md:items-center md:justify-between">
        <div className="flex items-center gap-3">
          <div className="flex size-10 items-center justify-center rounded-[8px] border border-cyan-300/25 bg-cyan-300/10 text-cyan-200 shadow-[0_0_24px_rgba(34,211,238,0.18)]">
            <Bot className="size-5" />
          </div>
          <div>
            <h2 className="text-xl font-semibold tracking-[0.18em] text-cyan-100">{assistantName}</h2>
            <div className="mt-1 flex items-center gap-2 text-xs text-emerald-300">
              <span className="size-2 rounded-full bg-emerald-400 shadow-[0_0_12px_rgba(52,211,153,0.9)]" />
              Online
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <div className="grid grid-cols-3 gap-2 text-xs text-cyan-100/80">
            <StatusPill icon={Radio} label="Runtime" value={runtimeState} />
            <StatusPill icon={ShieldCheck} label="Discord" value={discordState} />
            <StatusPill icon={Zap} label="Servicios" value={`${healthyServices}/${totalServices}`} />
          </div>
          <Button
            type="button"
            size="icon-lg"
            variant="outline"
            title={isExpanded ? "Contraer" : "Expandir"}
            aria-label={isExpanded ? "Contraer" : "Expandir"}
            onClick={() => setIsExpanded((value) => !value)}
            className="h-12 w-12 rounded-[8px] border-cyan-300/20 bg-cyan-950/50 text-cyan-100 hover:bg-cyan-900/60"
          >
            {isExpanded ? <Minimize2 className="size-4" /> : <Maximize2 className="size-4" />}
          </Button>
        </div>
      </div>

      <div className="assistance-layout grid min-h-0 grid-cols-1 xl:grid-cols-[300px_minmax(0,1fr)_380px]">
        <aside className="assistance-panel min-h-0 overflow-y-auto border-b border-cyan-300/10 p-4 xl:border-b-0 xl:border-r">
          <PanelHeader icon={BrainCircuit} title="Sistemas" />
          <div className="mt-4 space-y-3">
            <MetricBar label="CPU proxy" value={runtimeState === "healthy" ? 74 : 18} />
            <MetricBar label="Memoria agentes" value={healthyServices ? Math.round((healthyServices / Math.max(totalServices, 1)) * 100) : 0} />
            <MetricBar label="Discord bridge" value={discordState === "healthy" ? 88 : 22} />
          </div>

          <PanelHeader icon={Cpu} title="Agentes" className="mt-6" />
          <div className="mt-4 grid grid-cols-2 gap-2">
            {actionOptions.map((option) => {
              const Icon = option.icon;
              const active = activeAction === option.value;
              return (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => setActiveAction(option.value)}
                  className={`flex h-20 flex-col items-start justify-between rounded-[8px] border p-3 text-left transition ${active ? "border-cyan-300/60 bg-cyan-300/15 text-cyan-50" : "border-cyan-300/10 bg-cyan-950/20 text-cyan-100/70 hover:border-cyan-300/35"}`}
                >
                  <Icon className="size-4" />
                  <span className="text-sm font-medium">{option.label}</span>
                </button>
              );
            })}
          </div>
        </aside>

        <section className="relative flex min-h-0 flex-col items-center justify-center overflow-hidden border-b border-cyan-300/10 p-6 xl:border-b-0 xl:border-r">
          <div className="assistance-grid-bg absolute inset-0" />
          <div className={`assistance-core relative ${isListening ? "is-listening" : ""} ${isSending ? "is-thinking" : ""}`} aria-hidden="true">
            <span className="ring ring-one" />
            <span className="ring ring-two" />
            <span className="ring ring-three" />
            <span className="core-dot"><span /></span>
          </div>
          <div className="relative mt-8 text-center">
            <p className="text-2xl font-semibold tracking-[0.22em] text-cyan-100">{assistantName}</p>
            <p className="mt-3 inline-flex items-center gap-2 rounded-[8px] border border-cyan-300/10 bg-cyan-950/40 px-3 py-2 text-sm text-cyan-100/75">
              <span className={`size-2 rounded-full ${isListening ? "bg-emerald-300" : "bg-cyan-300"}`} />
              {isListening ? "Escuchando..." : isSending ? "Procesando..." : "Listo para recibir ordenes"}
            </p>
          </div>

          <div className="relative mt-12 flex items-center gap-4">
            <Button type="button" size="icon-lg" variant="outline" title="Dictar" aria-label="Dictar" onClick={toggleListening} className="size-14 rounded-[8px] border-cyan-300/20 bg-cyan-950/50 text-cyan-100 hover:bg-cyan-900/60">
              {isListening ? <MicOff className="size-5" /> : <Mic className="size-5" />}
            </Button>
            <Button type="button" size="icon-lg" variant="outline" title="Voz" aria-label="Voz" onClick={() => setIsSpeaking((value) => !value)} className="size-14 rounded-[8px] border-cyan-300/20 bg-cyan-950/50 text-cyan-100 hover:bg-cyan-900/60">
              {isSpeaking ? <Volume2 className="size-5" /> : <VolumeX className="size-5" />}
            </Button>
            <Button type="button" size="icon-lg" variant="outline" title="Enviar" aria-label="Enviar" onClick={() => void submitPrompt()} className="size-14 rounded-[8px] border-cyan-300/20 bg-cyan-950/50 text-cyan-100 hover:bg-cyan-900/60">
              <Send className="size-5" />
            </Button>
          </div>
        </section>

        <aside className="assistance-panel flex min-h-0 flex-col overflow-hidden p-4">
          <div className="shrink-0 flex items-center justify-between gap-3">
            <PanelHeader icon={Bot} title="Conversacion" />
            <select
              value={voiceName}
              onChange={(event) => setVoiceName(event.target.value)}
              className="h-8 max-w-[180px] rounded-[8px] border border-cyan-300/15 bg-cyan-950/60 px-2 text-xs text-cyan-100 outline-none"
              aria-label="Voz"
            >
              {voices.length ? voices.map((voice) => (
                <option key={`${voice.name}-${voice.lang}`} value={voice.name}>{voice.name}</option>
              )) : <option value="">Voz local</option>}
            </select>
          </div>

          <div ref={logRef} className="mt-4 min-h-0 flex-1 space-y-3 overflow-y-auto overscroll-contain pr-1">
            {messages.map((message) => (
              <div key={message.id} className={`rounded-[8px] border p-3 ${message.role === "user" ? "ml-8 border-emerald-300/20 bg-emerald-400/10" : message.role === "system" ? "border-amber-300/25 bg-amber-300/10" : "mr-8 border-cyan-300/15 bg-cyan-300/10"}`}>
                <p className="text-sm leading-6 text-cyan-50/90">{message.text}</p>
                <p className="mt-3 text-[11px] text-cyan-100/45">{message.time}</p>
              </div>
            ))}
          </div>

          <div className="mt-4 grid shrink-0 gap-2">
            <div className="flex flex-wrap gap-2">
              {quickPrompts.map((item) => (
                <button key={item} type="button" onClick={() => void submitPrompt(item)} className="rounded-[8px] border border-cyan-300/10 bg-cyan-950/40 px-3 py-2 text-left text-xs text-cyan-100/70 transition hover:border-cyan-300/35 hover:text-cyan-50">
                  {item}
                </button>
              ))}
            </div>
            <form className="flex gap-2" onSubmit={(event) => { event.preventDefault(); void submitPrompt(); }}>
              <textarea
                value={prompt}
                onChange={(event) => setPrompt(event.target.value)}
                placeholder="Escribe una peticion..."
                rows={2}
                className="min-h-[54px] flex-1 resize-none rounded-[8px] border border-cyan-300/15 bg-[#07131b] px-3 py-2 text-sm text-cyan-50 outline-none placeholder:text-cyan-100/35 focus:border-cyan-300/45"
              />
              <Button type="submit" disabled={isSending} size="icon-lg" aria-label="Enviar mensaje" className="h-[54px] w-12 rounded-[8px] bg-cyan-300 text-slate-950 hover:bg-cyan-200">
                {isSending ? <CheckCircle2 className="size-5 animate-pulse" /> : <Send className="size-5" />}
              </Button>
            </form>
          </div>
        </aside>
      </div>
    </div>
  );
}

function StatusPill({ icon: Icon, label, value }: { icon: typeof Bot; label: string; value: string }) {
  return (
    <div className="rounded-[8px] border border-cyan-300/10 bg-cyan-950/35 px-3 py-2">
      <div className="flex items-center gap-2 text-cyan-100/50">
        <Icon className="size-3.5" />
        <span>{label}</span>
      </div>
      <p className="mt-1 font-semibold text-cyan-100">{value}</p>
    </div>
  );
}

function PanelHeader({ icon: Icon, title, className = "" }: { icon: typeof Bot; title: string; className?: string }) {
  return (
    <div className={`flex items-center gap-2 text-cyan-100 ${className}`}>
      <Icon className="size-4 text-cyan-300" />
      <h3 className="text-sm font-semibold">{title}</h3>
    </div>
  );
}

function MetricBar({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <div className="mb-1 flex items-center justify-between text-xs text-cyan-100/65">
        <span>{label}</span>
        <span>{value}%</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-slate-800">
        <div className="h-full rounded-full bg-cyan-300 shadow-[0_0_14px_rgba(103,232,249,0.65)]" style={{ width: `${value}%` }} />
      </div>
    </div>
  );
}
