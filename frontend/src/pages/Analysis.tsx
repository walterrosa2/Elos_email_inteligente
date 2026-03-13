import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';
import DOMPurify from 'dompurify';
import { 
  Search, 
  FileText, 
  Mail, 
  Save, 
  CheckCircle, 
  AlertCircle, 
  HelpCircle, 
  ArrowRight,
  Eye,
  Database,
  Type,
  Filter
} from 'lucide-react';

interface JobSummary {
  id: number;
  status: string;
  simplified_status: string;
  sender: string;
  subject: string;
  attachment_name: string;
  received_at: string;
  criticality: string | null;
}

interface JobDetail extends JobSummary {
  extraction_result: Record<string, any> | null;
  storage_uri: string | null;
}

interface EmailContext {
  body_text: string | null;
  subject: string | null;
  sender: string | null;
  received_at: string | null;
  tone: string | null;
  summary: string | null;
  criticality_score: string | null;
  action_required: boolean;
}

export function Analysis() {
  const queryClient = useQueryClient();
  const [selectedJobId, setSelectedJobId] = useState<number | null>(null);
  const [activeTab, setActiveTab] = useState<'doc' | 'extraction' | 'email'>('doc');
  
  // Search and Filters
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [docTypeFilter, setDocTypeFilter] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [filenameFilter, setFilenameFilter] = useState('');
  const [criticalityFilter, setCriticalityFilter] = useState('');
  const [showFilters, setShowFilters] = useState(false);

  const [editedExtraction, setEditedExtraction] = useState<Record<string, any>>({});
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [fileType, setFileType] = useState<string | null>(null);

  // Fetch Jobs List
  const { data: jobsData, isLoading: isLoadingJobs } = useQuery({
    queryKey: ['jobs', searchTerm, statusFilter, docTypeFilter, startDate, endDate, filenameFilter, criticalityFilter],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (statusFilter) params.append('status_filter', statusFilter);
      if (docTypeFilter) params.append('doc_type', docTypeFilter);
      if (startDate) params.append('start_date', startDate);
      if (endDate) params.append('end_date', endDate);
      if (searchTerm) params.append('subject', searchTerm);
      if (filenameFilter) params.append('filename', filenameFilter);
      if (criticalityFilter) params.append('criticality', criticalityFilter);
      params.append('limit', '100');

      const response = await api.get('/api/v1/jobs', { params });
      return response.data;
    }
  });

  // Fetch Job Detail
  const { data: jobDetail } = useQuery<JobDetail>({
    queryKey: ['job-detail', selectedJobId],
    queryFn: async () => {
      const response = await api.get(`/api/v1/jobs/${selectedJobId}`);
      return response.data;
    },
    enabled: !!selectedJobId
  });

  // Fetch Contracts
  const { data: contractsData } = useQuery({
    queryKey: ['contracts-list'],
    queryFn: async () => {
      const resp = await api.get('/api/v1/contracts');
      return resp.data;
    }
  });

  // Fetch Email Context
  const { data: emailContext } = useQuery<EmailContext>({
    queryKey: ['email-context', selectedJobId],
    queryFn: async () => {
      const response = await api.get(`/api/v1/jobs/${selectedJobId}/email`);
      return response.data;
    },
    enabled: !!selectedJobId
  });

  // Update Extraction Mutation
  const updateMutation = useMutation({
    mutationFn: async (newData: Record<string, any>) => {
      await api.patch(`/api/v1/jobs/${selectedJobId}/extraction`, {
        extraction_result: newData
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['job-detail', selectedJobId] });
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
      alert('Extração atualizada com sucesso!');
    }
  });

  // Load PDF Blob when job changes
  useEffect(() => {
    if (selectedJobId) {
      const fetchFile = async () => {
        try {
          // Add a cache breaker or ensure absolute URL if needed, 
          // but mainly ensure the blob is handled.
          const response = await api.get(`/api/v1/jobs/${selectedJobId}/file`, {
            responseType: 'arraybuffer'
          });
          const contentType = response.headers['content-type'] || 'application/pdf';
          const blob = new Blob([response.data], { type: contentType });
          const url = URL.createObjectURL(blob);
          setPdfUrl(url);
          setFileType(contentType);
        } catch (err) {
          console.error("Erro ao carregar arquivo:", err);
          setPdfUrl(null);
          setFileType(null);
        }
      };
      fetchFile();
    } else {
      setPdfUrl(null);
    }
    
    // Reset tabs and extraction when job changes
    setActiveTab('doc');
    return () => {
      if (pdfUrl) {
        URL.revokeObjectURL(pdfUrl);
      }
    };
  }, [selectedJobId]);

  // Sync edited extraction when job detail loads
  useEffect(() => {
    if (jobDetail?.extraction_result) {
      setEditedExtraction(jobDetail.extraction_result);
    } else {
      setEditedExtraction({});
    }
  }, [jobDetail]);

  const jobs: JobSummary[] = jobsData?.items || [];

  const handleSave = () => {
    updateMutation.mutate(editedExtraction);
  };

  const updateField = (key: string, value: any) => {
    setEditedExtraction(prev => ({ ...prev, [key]: value }));
  };

  return (
    <div className="flex h-[calc(100vh-64px)] overflow-hidden bg-slate-50">
      {/* LEFT PANEL: Job List (Outlook Style) */}
      <div className="w-1/3 min-w-[350px] border-r border-slate-200 bg-white flex flex-col z-10">
        <div className="p-4 border-b border-slate-100 bg-slate-50/50 flex flex-col gap-3">
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
              <input 
                type="text" 
                placeholder="Buscar assunto..." 
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-white border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-indigo-500 outline-none shadow-sm transition-all"
              />
            </div>
            <button 
              onClick={() => setShowFilters(!showFilters)}
              className={`p-2 rounded-xl flex items-center justify-center border transition-all ${
                showFilters || statusFilter || docTypeFilter || startDate || endDate || filenameFilter || criticalityFilter
                  ? 'bg-indigo-50 border-indigo-200 text-indigo-600' 
                  : 'bg-white border-slate-200 text-slate-500 hover:bg-slate-50'
              }`}
              title="Filtros Avançados"
            >
               <Filter size={18} />
            </button>
          </div>

          {showFilters && (
            <div className="flex flex-col gap-2 p-3 bg-white border border-slate-200 rounded-xl shadow-sm animate-in fade-in slide-in-from-top-2">
               <input 
                  type="text" 
                  placeholder="Nome do anexo..." 
                  value={filenameFilter}
                  onChange={e => setFilenameFilter(e.target.value)}
                  className="w-full px-3 py-1.5 border border-slate-200 text-sm rounded-lg outline-none focus:border-indigo-500"
               />
               <select 
                  value={statusFilter}
                  onChange={e => setStatusFilter(e.target.value)}
                  className="w-full px-3 py-1.5 border border-slate-200 text-sm rounded-lg outline-none focus:border-indigo-500"
               >
                  <option value="">Status (Todos)</option>
                  <option value="Concluído">Concluídos</option>
                  <option value="Não mapeado">Não Mapeados</option>
                  <option value="Erro">Com Erro</option>
               </select>
               <select 
                  value={criticalityFilter}
                  onChange={e => setCriticalityFilter(e.target.value)}
                  className="w-full px-3 py-1.5 border border-slate-200 text-sm rounded-lg outline-none focus:border-indigo-500"
               >
                  <option value="">Criticidade (Todas)</option>
                  <option value="BAIXA">Baixa</option>
                  <option value="MEDIA">Média</option>
                  <option value="ALTA">Alta</option>
                  <option value="CRITICA">Crítica</option>
               </select>
               <select 
                  value={docTypeFilter}
                  onChange={e => setDocTypeFilter(e.target.value)}
                  className="w-full px-3 py-1.5 border border-slate-200 text-sm rounded-lg outline-none focus:border-indigo-500"
               >
                  <option value="">Tipo (Todos)</option>
                  {contractsData?.map((c: any) => (
                    <option key={c.doc_type} value={c.doc_type}>{c.doc_type}</option>
                  ))}
                  <option value="UNKNOWN">Não Mapeado</option>
               </select>
               <div className="flex gap-2 items-center">
                  <input 
                     type="date"
                     title="Data De" 
                     value={startDate}
                     onChange={e => setStartDate(e.target.value)}
                     className="w-1/2 px-2 py-1.5 border border-slate-200 text-xs rounded-lg outline-none focus:border-indigo-500"
                  />
                  <input 
                     type="date"
                     title="Data Até" 
                     value={endDate}
                     onChange={e => setEndDate(e.target.value)}
                     className="w-1/2 px-2 py-1.5 border border-slate-200 text-xs rounded-lg outline-none focus:border-indigo-500"
                  />
               </div>
            </div>
          )}
        </div>

        <div className="flex-1 overflow-y-auto">
          {isLoadingJobs ? (
            <div className="p-8 text-center bg-white">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto mb-4"></div>
              <p className="text-slate-400">Carregando fila...</p>
            </div>
          ) : jobs.length === 0 ? (
            <div className="p-8 text-center text-slate-400">
              <Mail className="mx-auto mb-4 opacity-20" size={48} />
              <p>Nenhum e-mail disponível</p>
            </div>
          ) : (
            <div className="divide-y divide-slate-50">
              {jobs.map((job) => (
                <div 
                  key={job.id} 
                  onClick={() => setSelectedJobId(job.id)}
                  className={`p-4 cursor-pointer transition-all hover:bg-indigo-50/30 group ${
                    selectedJobId === job.id ? 'bg-indigo-50 border-l-4 border-indigo-600' : ''
                  }`}
                >
                  <div className="flex justify-between items-start mb-1">
                    <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full ${
                      job.simplified_status === 'Concluído' ? 'bg-emerald-100 text-emerald-700' :
                      job.simplified_status === 'Não mapeado' ? 'bg-amber-100 text-amber-700' :
                      'bg-rose-100 text-rose-700'
                    }`}>
                      {job.simplified_status}
                    </span>
                    <span className="text-xs text-slate-400">
                      {new Date(job.received_at).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' })}
                    </span>
                  </div>
                  <h4 className={`font-semibold text-slate-800 truncate mb-1 ${selectedJobId === job.id ? 'text-indigo-900' : ''}`}>
                    {job.subject || '(Sem Assunto)'}
                  </h4>
                  <p className="text-sm text-slate-500 truncate mb-1.5">{job.sender}</p>
                  
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <div className="flex items-center gap-1 text-[11px] text-slate-400 italic bg-white px-1.5 py-0.5 border border-slate-100 rounded-md flex-1 min-w-0">
                      <FileText size={12} className="shrink-0" />
                      <span className="truncate">{job.attachment_name}</span>
                    </div>
                    {job.criticality && (
                       <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded leading-none shrink-0 ${
                         job.criticality === 'CRITICA' ? 'bg-rose-100 text-rose-700' :
                         job.criticality === 'ALTA' ? 'bg-orange-100 text-orange-700' :
                         job.criticality === 'MEDIA' ? 'bg-blue-100 text-blue-700' :
                         'bg-emerald-100 text-emerald-700'
                       }`}>
                         {job.criticality}
                       </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* RIGHT PANEL: Detail View */}
      <div className="flex-1 flex flex-col overflow-hidden bg-white">
        {!selectedJobId ? (
          <div className="flex-1 flex flex-col items-center justify-center text-slate-300 p-12">
            <div className="relative mb-6">
              <Mail size={120} className="opacity-10" />
              <ArrowRight className="absolute bottom-4 -right-8 animate-bounce" size={40} />
            </div>
            <h2 className="text-2xl font-semibold text-slate-400">Selecione um e-mail para análise</h2>
            <p className="max-w-xs text-center mt-2">Veja os dados extraídos pela IA lado a lado com o documento original.</p>
          </div>
        ) : (
          <>
            {/* Header Metadata */}
            <div className="p-6 border-b border-slate-100">
              <div className="flex justify-between items-start">
                <div>
                  <h2 className="text-2xl font-bold text-slate-800">{jobDetail?.subject}</h2>
                  <div className="flex items-center gap-4 mt-2 text-slate-500">
                    <div className="flex items-center gap-1.5">
                      <Mail size={16} className="text-indigo-400" />
                      <span className="text-sm">{jobDetail?.sender}</span>
                    </div>
                    <div className="h-1 w-1 rounded-full bg-slate-300"></div>
                    <div className="text-sm">
                      {jobDetail?.received_at && new Date(jobDetail.received_at).toLocaleString('pt-BR')}
                    </div>
                  </div>
                </div>
                
                <div className="flex gap-2">
                  <button 
                    onClick={handleSave}
                    disabled={updateMutation.isPending}
                    className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-xl font-medium transition-all shadow-lg shadow-indigo-200 disabled:opacity-50"
                  >
                    <Save size={18} />
                    {updateMutation.isPending ? 'Salvando...' : 'Salvar Validação'}
                  </button>
                </div>
              </div>

              {/* Tabs */}
              <div className="flex items-center gap-6 mt-6 border-b border-slate-100">
                <button 
                  onClick={() => setActiveTab('doc')}
                  className={`pb-3 text-sm font-semibold transition-all border-b-2 ${
                    activeTab === 'doc' ? 'text-indigo-600 border-indigo-600' : 'text-slate-400 border-transparent hover:text-slate-600'
                  } flex items-center gap-2`}
                >
                  <Eye size={16} />
                  Documento Original
                </button>
                <button 
                  onClick={() => setActiveTab('extraction')}
                  className={`pb-3 text-sm font-semibold transition-all border-b-2 ${
                    activeTab === 'extraction' ? 'text-indigo-600 border-indigo-600' : 'text-slate-400 border-transparent hover:text-slate-600'
                  } flex items-center gap-2`}
                >
                  <Database size={16} />
                  Dados Extraídos (IA)
                </button>
                <button 
                  onClick={() => setActiveTab('email')}
                  className={`pb-3 text-sm font-semibold transition-all border-b-2 ${
                    activeTab === 'email' ? 'text-indigo-600 border-indigo-600' : 'text-slate-400 border-transparent hover:text-slate-600'
                  } flex items-center gap-2`}
                >
                  <Type size={16} />
                  Corpo do E-mail
                </button>
              </div>
            </div>

            {/* Tab Content */}
            <div className="flex-1 overflow-hidden bg-slate-50 p-6">
              {activeTab === 'doc' && (
                <div className="w-full h-full bg-slate-200 rounded-2xl overflow-hidden shadow-inner flex items-center justify-center relative">
                  {pdfUrl ? (
                    (fileType?.includes('pdf') || jobDetail?.attachment_name?.toLowerCase().endsWith('.pdf')) ? (
                      <object 
                        data={`${pdfUrl}#view=FitH`} 
                        type="application/pdf"
                        className="w-full h-full border-none rounded-2xl"
                      >
                         <div className="w-full h-full flex flex-col items-center justify-center p-8 bg-slate-100 text-slate-500 rounded-2xl">
                           <FileText size={48} className="mb-4 text-slate-400" />
                           <h3 className="text-lg font-medium text-slate-700 mb-2">Pré-visualização Nativamente Bloqueada</h3>
                           <p className="text-sm text-center mb-6 max-w-sm">
                             O seu navegador bloqueou a renderização do PDF pela engine local.
                           </p>
                           <a 
                             href={pdfUrl} 
                             download={jobDetail?.attachment_name || 'documento.pdf'} 
                             className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl font-medium shadow-sm transition-all"
                           >
                             Baixar para Visualizar
                           </a>
                         </div>
                      </object>
                    ) : (
                      <div className="w-full h-full overflow-auto flex flex-col items-center justify-center p-4">
                        <img 
                          src={pdfUrl} 
                          alt="Anexo" 
                          className="max-w-full max-h-full object-contain shadow-lg rounded-lg mb-4"
                          onError={(e) => {
                             e.currentTarget.style.display = 'none';
                             const parent = e.currentTarget.parentElement;
                             if(parent && !parent.querySelector('.fallback-file')) {
                                parent.innerHTML = `
                               <div class="fallback-file flex flex-col items-center text-center p-8 bg-white rounded-2xl shadow-sm border border-slate-100 max-w-sm m-auto">
                                 <div class="h-20 w-20 bg-slate-100 text-slate-400 rounded-full flex items-center justify-center mx-auto mb-4">
                                   <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-file"><path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/></svg>
                                 </div>
                                 <p class="font-medium text-slate-800 text-lg mb-1">Visualização Indisponível</p>
                                 <p class="text-xs text-slate-500 mb-6 break-all line-clamp-2">${jobDetail?.attachment_name || 'Arquivo anexado'}</p>
                                 <a href="${pdfUrl}" download="${jobDetail?.attachment_name || 'arquivo'}" class="bg-indigo-600 text-white px-6 py-2 rounded-lg hover:bg-indigo-700 font-medium transition-colors shadow-sm">Baixar Arquivo</a>
                               </div>
                                `;
                             }
                          }}
                        />
                      </div>
                    )
                  ) : (
                    <div className="text-center">
                       <HelpCircle size={48} className="mx-auto text-slate-400 mb-4 opacity-50" />
                       <p className="text-slate-500">Arquivo não disponível para pré-visualização.</p>
                       <p className="text-xs text-slate-400 mt-2">{jobDetail?.attachment_name}</p>
                    </div>
                  )}
                </div>
              )}

              {activeTab === 'extraction' && (
                <div className="bg-white rounded-2xl p-8 shadow-sm border border-slate-100 h-full overflow-y-auto">
                  <div className="flex items-center gap-3 mb-6">
                    <div className="p-2 bg-indigo-50 rounded-lg text-indigo-600">
                       <CheckCircle size={24} />
                    </div>
                    <div>
                      <h3 className="text-xl font-bold text-slate-800">Campos Reconhecidos</h3>
                      <p className="text-sm text-slate-500">A IA detectou estes campos. Corrija se necessário.</p>
                    </div>
                  </div>
                  
                  {Object.keys(editedExtraction).length === 0 ? (
                    <div className="p-8 text-center text-slate-400 border-2 border-dashed border-slate-100 rounded-xl">
                      <AlertCircle className="mx-auto mb-2 opacity-30" size={32} />
                      <p>Nenhum dado extraído disponível.</p>
                    </div>
                  ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      {Object.entries(editedExtraction).map(([key, value]) => (
                        <div key={key} className="space-y-1.5">
                          <label className="text-xs font-bold text-slate-400 uppercase tracking-wider ml-1">
                            {key.replace(/_/g, ' ')}
                          </label>
                          <input 
                            type="text" 
                            value={String(value)}
                            onChange={(e) => updateField(key, e.target.value)}
                            className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none transition-all text-slate-700"
                          />
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {activeTab === 'email' && (
                <div className="bg-white rounded-2xl p-8 shadow-sm border border-slate-100 h-full overflow-y-auto">
                    {/* IA Analysis Header if exists */}
                    {emailContext?.summary && (
                      <div className="mb-6 grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="p-4 bg-indigo-50 border border-indigo-100 rounded-xl">
                          <label className="text-[10px] font-bold text-indigo-400 uppercase tracking-widest block mb-1">Tom da Comunicação</label>
                          <span className="text-indigo-900 font-semibold">{emailContext.tone || 'Neutro'}</span>
                        </div>
                        <div className={`p-4 border rounded-xl ${
                          emailContext.criticality_score === 'CRITICA' || emailContext.criticality_score === 'ALTA' 
                            ? 'bg-rose-50 border-rose-100 text-rose-900' 
                            : 'bg-emerald-50 border-emerald-100 text-emerald-900'
                        }`}>
                          <label className="text-[10px] font-bold opacity-60 uppercase tracking-widest block mb-1">Criticidade</label>
                          <span className="font-bold">{emailContext.criticality_score || 'BAIXA'}</span>
                        </div>
                        <div className="p-4 bg-amber-50 border border-amber-100 rounded-xl md:col-span-1">
                          <label className="text-[10px] font-bold text-amber-600 uppercase tracking-widest block mb-1">Ação Sugerida</label>
                          <span className="text-amber-900 text-sm font-medium">
                            {emailContext.action_required ? '⚠️ Ação Necessária' : 'Nenhuma ação imediata'}
                          </span>
                        </div>
                        <div className="p-4 bg-slate-50 border border-slate-100 rounded-xl md:col-span-3">
                          <label className="text-[10px] font-bold text-slate-400 uppercase tracking-widest block mb-1">Resumo Executivo (IA)</label>
                          <p className="text-slate-700 text-sm leading-relaxed">{emailContext.summary}</p>
                        </div>
                      </div>
                    )}

                    <div className="prose prose-sm md:prose-base max-w-none">
                      <div 
                        className="bg-white p-6 rounded-xl border border-slate-200 text-slate-800 shadow-sm overflow-x-auto min-h-[300px]"
                        dangerouslySetInnerHTML={{
                          __html: emailContext?.body_text 
                            ? DOMPurify.sanitize(emailContext.body_text, { USE_PROFILES: { html: true } })
                            : "<p class='text-slate-400'>O corpo deste e-mail está vazio ou não pôde ser recuperado.</p>"
                        }}
                      />
                    </div>
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
