import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';
import { Settings as SettingsIcon, Save, TerminalSquare, FileDigit } from 'lucide-react';

interface SystemSetting {
  key: string;
  value: any;
  description: string;
}

export function Settings() {
  const queryClient = useQueryClient();

  const [prompt, setPrompt] = useState('Extraia as principais informações pertinentes deste documento (faturas, valores, datas, nomes) em um formato JSON chave-valor.');
  const [promptIdentificacao, setPromptIdentificacao] = useState('Analyze the following document text and classify it into one of the provided Document Types.\nIf the document does not fit any of these types closely, classify as \'unknown\'.\n\nReturn a JSON object with:\n- "doc_type": The best matching document type (or "unknown").\n- "confidence": A float between 0.0 and 1.0 indicating certainty.\n- "reasoning": A brief explanation of why this type was chosen, citing specific content matches.');
  const [promptCriticidade, setPromptCriticidade] = useState('Você é um auditor sênior de comunicações corporativas.\nAnalise o corpo do e-mail e extraia as seguintes informações em formato JSON:\n\n1. "resumo": Uma frase curta resumindo a solicitação.\n2. "tom": O tom da conversa (Ex: "Formal", "Amigável", "Agressivo", "Urgente", "Nervoso").\n3. "criticidade": Nível de urgência/risco (1 a 5, onde 5 é Crítico).\n4. "acao_necessaria": true/false (Se requer ação humana imediata).\n\nCritérios de Criticidade:\n- 5 (CRITICA): Ameaça de cancelamento, risco jurídico, prazos vencidos hoje, pagamentos atrasados bloqueando serviço.\n- 4 (ALTA): Solicitação de prioridade explícita ("Urgente", "ASAP"), diretores envolvidos.\n- 3 (MEDIA): Solicitação padrão com prazo.\n- 1-2 (BAIXA): Informativos, agradecimentos, conversa de rotina.');
  const [extensions, setExtensions] = useState('.pdf, .xml, .jpeg, .jpg, .png');

  const { data: settings = [], isLoading } = useQuery<SystemSetting[]>({
    queryKey: ['settings'],
    queryFn: async () => {
      const resp = await api.get('/api/v1/settings');
      return resp.data;
    }
  });

  useEffect(() => {
    if (settings.length > 0) {
      const ptInfo = settings.find(s => s.key === 'openai_prompt_padrao');
      if (ptInfo) setPrompt(ptInfo.value);

      const ptClass = settings.find(s => s.key === 'openai_prompt_identificacao');
      if (ptClass) setPromptIdentificacao(ptClass.value);

      const ptCrit = settings.find(s => s.key === 'openai_prompt_criticidade');
      if (ptCrit) setPromptCriticidade(ptCrit.value);

      const extInfo = settings.find(s => s.key === 'allowed_extensions');
      if (extInfo && Array.isArray(extInfo.value)) {
        setExtensions(extInfo.value.join(', '));
      }
    }
  }, [settings]);

  const saveMutation = useMutation({
    mutationFn: async (payload: SystemSetting[]) => {
      // Execute the updates sequentially
      for (const setting of payload) {
         await api.put(`/api/v1/settings/${setting.key}`, setting);
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings'] });
      alert('Configurações salvas com sucesso!');
    }
  });

  const handleSaveAll = () => {
    const extsArray = extensions.split(',').map(e => e.trim().toLowerCase()).filter(Boolean);
    saveMutation.mutate([
      { key: 'openai_prompt_padrao', value: prompt, description: 'Prompt genérico de extração, atuando como fallback caso um tipo não tenha prompt específico.' },
      { key: 'openai_prompt_identificacao', value: promptIdentificacao, description: 'Prompt que orienta como a IA deve analisar o texto e eleger o tipo do documento.' },
      { key: 'openai_prompt_criticidade', value: promptCriticidade, description: 'Prompt que audita os e-mails, definindo o tom e criticidade antes da triagem.' },
      { key: 'allowed_extensions', value: extsArray, description: 'Extensões permitidas na ingestão via e-mails.' }
    ]);
  }

  if (isLoading) return <div className="p-8 text-slate-500">Carregando Configurações...</div>;

  return (
    <div className="p-8 max-w-5xl mx-auto">
      <div className="flex items-center gap-4 mb-8">
        <div className="h-12 w-12 bg-slate-900 text-white rounded-xl flex items-center justify-center shadow-lg">
          <SettingsIcon size={24} />
        </div>
        <div>
          <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Configurações do Sistema</h1>
          <p className="text-slate-500 mt-1">Gerencie fluxos e diretrizes base da IA (Acesso Restrito).</p>
        </div>
      </div>

      <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden mb-6">
        <div className="p-6 border-b border-slate-200">
          <h2 className="text-lg font-bold text-slate-800 flex items-center gap-2">
            <TerminalSquare className="text-indigo-600" size={20} />
            [Classificação] Prompt de Identificação de Tipo
          </h2>
          <p className="text-sm text-slate-500 mt-1 mb-4">Instrui a IA sobre como descobrir qual é o tipo correto de um documento baseado em seu texto. <br/><span className="text-indigo-600 font-semibold bg-indigo-50 px-2 py-0.5 rounded">Nota: O texto do documento e a lista de contratos disponíveis são injetados automaticamente no final deste prompt pelo sistema.</span></p>
          
          <textarea 
             rows={9}
             value={promptIdentificacao}
             onChange={(e) => setPromptIdentificacao(e.target.value)}
             className="w-full border border-slate-300 rounded-xl px-5 py-4 font-mono text-sm leading-relaxed focus:ring-2 focus:ring-indigo-500 outline-none bg-slate-900 text-sky-400 shadow-inner resize-y"
             placeholder="Digite o Prompt de Identificação aqui..."
             spellCheck={false}
          />
        </div>
      
        <div className="p-6 border-b border-slate-200 bg-slate-50/50">
          <h2 className="text-lg font-bold text-slate-800 flex items-center gap-2">
            <TerminalSquare className="text-indigo-600" size={20} />
            [Análise] Prompt de Criticidade (Auditoria de E-mail)
          </h2>
          <p className="text-sm text-slate-500 mt-1 mb-4">Instrui a IA a interpretar o corpo do e-mail recebido, categorizando seu grau de importância e tom da mensagem, além de gerar um resumo antes da extração de documentos. <br/><span className="text-indigo-600 font-semibold bg-indigo-50 px-2 py-0.5 rounded">Nota: O assunto e o texto original do e-mail chegarão ao final deste prompt automaticamente.</span></p>
          
          <textarea 
             rows={12}
             value={promptCriticidade}
             onChange={(e) => setPromptCriticidade(e.target.value)}
             className="w-full border border-slate-300 rounded-xl px-5 py-4 font-mono text-sm leading-relaxed focus:ring-2 focus:ring-indigo-500 outline-none bg-slate-900 text-amber-400 shadow-inner resize-y"
             placeholder="Digite o Prompt de Criticidade aqui..."
             spellCheck={false}
          />
        </div>

        <div className="p-6 border-b border-slate-200">
          <h2 className="text-lg font-bold text-slate-800 flex items-center gap-2">
            <TerminalSquare className="text-indigo-600" size={20} />
            [Extração] Prompt Genérico de Fallback
          </h2>
          <p className="text-sm text-slate-500 mt-1 mb-6">Este prompt é acionado como um plano B, executando a extração caso o documento tenha sido classificado como um tipo desconhecido.</p>
          
          <textarea 
             rows={5}
             value={prompt}
             onChange={(e) => setPrompt(e.target.value)}
             className="w-full border border-slate-300 rounded-xl px-5 py-4 font-mono text-sm leading-relaxed focus:ring-2 focus:ring-indigo-500 outline-none bg-slate-900 text-green-400 shadow-inner resize-y"
             placeholder="Digite o Prompt Base aqui..."
             spellCheck={false}
          />
        </div>

        <div className="p-6 border-b border-slate-200">
          <h2 className="text-lg font-bold text-slate-800 flex items-center gap-2">
            <FileDigit className="text-indigo-600" size={20} />
            Extensões Permitidas (Ingestão)
          </h2>
          <p className="text-sm text-slate-500 mt-1 mb-6">Liste as extensões de arquivos que a Ingestão Automática considerará válidas (separados por vírgula).</p>
          
          <input 
             type="text"
             value={extensions}
             onChange={(e) => setExtensions(e.target.value)}
             className="w-full border border-slate-300 rounded-xl px-5 py-4 text-sm focus:ring-2 focus:ring-indigo-500 outline-none bg-white font-medium text-slate-700 shadow-sm"
             placeholder="ex: .pdf, .xml, .jpeg"
          />
        </div>

        <div className="p-6 bg-slate-50 flex justify-end">
          <button 
             onClick={handleSaveAll}
             disabled={saveMutation.isPending}
             className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-2 rounded-lg font-medium transition-colors shadow-sm disabled:opacity-50"
          >
            <Save size={18} />
            {saveMutation.isPending ? 'Salvando...' : 'Salvar Alterações Globais'}
          </button>
        </div>
      </div>
    </div>
  );
}
