import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';
import { 
  FileText, 
  FolderCheck, 
  RefreshCcw, 
  Search, 
  CheckCircle, 
  AlertCircle, 
  Calendar, 
  Filter,
  CheckSquare,
  Square,
  ChevronLeft,
  ChevronRight,
  Send,
  ExternalLink
} from 'lucide-react';

interface JobSummary {
  id: number;
  status: string;
  simplified_status: string;
  sender: string;
  subject: string;
  attachment_name: string;
  received_at: string;
  doc_type: string | null;
  direction_status: string;
  routed_at: string | null;
  routed_path: string | null;
  target_payment_date: string | null;
  extraction_result: Record<string, any> | null;
  detected_due_date?: string | null;
  due_date_source?: string | null;
  due_date_context?: string | null;
  original_due_date?: string | null;
  email_body_due_date?: string | null;
}

export function Routing() {
  const queryClient = useQueryClient();
  const [searchTerm, setSearchTerm] = useState('');
  const [directionFilter, setDirectionFilter] = useState('PENDING'); // PENDING, ROUTED, FAILED
  const [docTypeFilter, setDocTypeFilter] = useState('');
  const [dueDateFilter, setDueDateFilter] = useState('ALL'); // ALL, WITH_DUE, NO_DUE
  const [page, setPage] = useState(1);
  const limit = 15;

  // Selection list for batch actions
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [customDateJobId, setCustomDateJobId] = useState<number | null>(null);
  const [customDate, setCustomDate] = useState('');

  // Inspection states (Split View V4.0)
  const [inspectedJob, setInspectedJob] = useState<JobSummary | null>(null);
  const [emailContext, setEmailContext] = useState<any>(null);
  const [isEmailLoading, setIsEmailLoading] = useState(false);
  const [fileUrl, setFileUrl] = useState<string>('');
  const [isFileLoading, setIsFileLoading] = useState(false);

  const loadFile = async (jobId: number) => {
    setIsFileLoading(true);
    setFileUrl('');
    try {
      const resp = await api.get(`/api/v1/jobs/${jobId}/file`, { responseType: 'blob' });
      const blob = new Blob([resp.data], { type: resp.headers['content-type'] || 'application/pdf' });
      const url = URL.createObjectURL(blob);
      setFileUrl(url);
    } catch (e) {
      console.error("Erro ao carregar arquivo:", e);
      setFileUrl('');
    } finally {
      setIsFileLoading(false);
    }
  };

  const handleInspect = async (job: JobSummary) => {
    if (inspectedJob?.id === job.id) {
      setInspectedJob(null);
      setEmailContext(null);
      setFileUrl('');
      return;
    }
    setInspectedJob(job);
    loadFile(job.id);
    setIsEmailLoading(true);
    try {
      const resp = await api.get(`/api/v1/jobs/${job.id}/email`);
      setEmailContext(resp.data);
    } catch (e) {
      console.error(e);
      setEmailContext(null);
    } finally {
      setIsEmailLoading(false);
    }
  };

  // Fetch Jobs List for Routing
  const { data: jobsData, isLoading, isFetching } = useQuery({
    queryKey: ['routing-jobs', searchTerm, directionFilter, docTypeFilter, dueDateFilter, page],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (searchTerm) params.append('filename', searchTerm);
      if (directionFilter && directionFilter !== 'ALL') {
        params.append('direction_status', directionFilter);
      }
      if (docTypeFilter) params.append('doc_type', docTypeFilter);
      
      // Filtro de vencimento inteligente (V4.0)
      if (dueDateFilter === 'WITH_DUE') {
        params.append('has_due_date', 'true');
      } else if (dueDateFilter === 'NO_DUE') {
        params.append('has_due_date', 'false');
      }

      params.append('skip', ((page - 1) * limit).toString());
      params.append('limit', limit.toString());

      const response = await api.get('/api/v1/jobs', { params });
      return response.data;
    }
  });

  // Fetch Contracts (for Filter)
  const { data: contractsData } = useQuery({
    queryKey: ['contracts-list'],
    queryFn: async () => {
      const resp = await api.get('/api/v1/contracts');
      return resp.data;
    }
  });

  // Route Mutation
  const routeMutation = useMutation({
    mutationFn: async ({ id, customPaymentDate }: { id: number; customPaymentDate?: string }) => {
      await api.post(`/api/v1/jobs/${id}/route`, {
        custom_payment_date: customPaymentDate || null
      });
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['routing-jobs'] });
      setSelectedIds(prev => prev.filter(x => x !== variables.id));
      setCustomDateJobId(null);
      setCustomDate('');
      
      // Se estiver inspecionando este job, fecha/atualiza
      if (inspectedJob?.id === variables.id) {
         setInspectedJob(null);
         setEmailContext(null);
         setFileUrl('');
      }
    },
    onError: (err: any) => {
      alert(`Erro ao direcionar arquivo: ${err?.response?.data?.detail || err.message}`);
    }
  });

  // Batch Route Mutation
  const routeBatchMutation = useMutation({
    mutationFn: async (ids: number[]) => {
      for (const id of ids) {
        await api.post(`/api/v1/jobs/${id}/route`);
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['routing-jobs'] });
      setSelectedIds([]);
      setInspectedJob(null);
      setEmailContext(null);
      setFileUrl('');
      alert('Arquivos selecionados direcionados com sucesso!');
    },
    onError: (err: any) => {
      alert(`Erro no direcionamento em lote: ${err?.response?.data?.detail || err.message}`);
    }
  });

  const jobs: JobSummary[] = jobsData?.items || [];
  const total = jobsData?.total || 0;
  const totalPages = Math.ceil(total / limit);

  const toggleSelectAll = () => {
    if (selectedIds.length === jobs.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(jobs.map(j => j.id));
    }
  };

  const toggleSelect = (id: number) => {
    setSelectedIds(prev => 
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    );
  };

  const handleRouteSingle = (id: number) => {
    routeMutation.mutate({ id });
  };

  const handleRouteCustom = (id: number) => {
    if (!customDate) {
      alert('Selecione uma data para direcionar.');
      return;
    }
    routeMutation.mutate({ id, customPaymentDate: customDate });
  };

  const handleRouteBatch = () => {
    if (selectedIds.length === 0) return;
    if (confirm(`Deseja direcionar os ${selectedIds.length} arquivos selecionados de forma automatica?`)) {
      routeBatchMutation.mutate(selectedIds);
    }
  };

  // Helper to extract display date from Job summary
  const getReferenceDate = (job: JobSummary) => {
    if (job.detected_due_date) {
      const parts = job.detected_due_date.split('-');
      if (parts.length === 3) return `${parts[2]}/${parts[1]}/${parts[0]}`;
      return job.detected_due_date;
    }
    if (!job.extraction_result) return 'Sem extração';
    const docType = job.doc_type || '';
    const extracted = job.extraction_result;
    
    if (docType.toLowerCase().includes('boleto')) {
      const val = extracted.data_vencimento || extracted.vencimento || 'N/A';
      return val;
    }
    return extracted.emissao || extracted.data_emissao || 'N/A';
  };

  return (
    <div className="p-8 bg-slate-50 min-h-screen">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-8 gap-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-800 flex items-center gap-3 font-display">
            <FolderCheck className="text-indigo-600" size={32} />
            Direcionamento de Pagamentos
          </h1>
          <p className="text-slate-500 mt-1">
            Controle e envie arquivos validados para as pastas mensais do servidor financeiro.
          </p>
        </div>

        <div className="flex gap-3">
          {selectedIds.length > 0 && (
            <button
              onClick={handleRouteBatch}
              disabled={routeBatchMutation.isPending}
              className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white px-5 py-2.5 rounded-xl font-semibold transition-all shadow-lg shadow-emerald-100 disabled:opacity-50"
            >
              <Send size={18} />
              Direcionar Selecionados ({selectedIds.length})
            </button>
          )}
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm flex items-center justify-between">
          <div>
            <span className="text-sm font-semibold text-slate-400 block mb-1">Aguardando Direcionamento</span>
            <span className="text-3xl font-bold text-slate-800">
              {directionFilter === 'PENDING' ? total : '-'}
            </span>
          </div>
          <div className="p-4 bg-amber-50 rounded-2xl text-amber-600">
            <Calendar size={28} />
          </div>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm flex items-center justify-between">
          <div>
            <span className="text-sm font-semibold text-slate-400 block mb-1">Roteados no Servidor</span>
            <span className="text-3xl font-bold text-slate-800">
              {directionFilter === 'ROUTED' ? total : '-'}
            </span>
          </div>
          <div className="p-4 bg-emerald-50 rounded-2xl text-emerald-600">
            <CheckCircle size={28} />
          </div>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm flex items-center justify-between">
          <div>
            <span className="text-sm font-semibold text-slate-400 block mb-1">Falhas de Envio</span>
            <span className="text-3xl font-bold text-slate-800">
              {directionFilter === 'FAILED' ? total : '-'}
            </span>
          </div>
          <div className="p-4 bg-rose-50 rounded-2xl text-rose-600">
            <AlertCircle size={28} />
          </div>
        </div>
      </div>

      {/* Split-Screen Layout wrapper */}
      <div className="flex flex-col lg:flex-row gap-6 items-start">
        
        {/* Lado Esquerdo: Filtros e Tabela de Documentos */}
        <div className={`flex-1 w-full transition-all duration-300 ${inspectedJob ? 'lg:max-w-[55%]' : ''}`}>
          
          {/* Filtering and Search Bar */}
          <div className="bg-white p-4 rounded-2xl border border-slate-100 shadow-sm flex flex-col md:flex-row gap-4 mb-6 items-center">
            <div className="relative flex-1 w-full">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
              <input 
                type="text" 
                placeholder="Buscar por nome de anexo..."
                value={searchTerm}
                onChange={(e) => { setSearchTerm(e.target.value); setPage(1); }}
                className="w-full pl-11 pr-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-indigo-500 outline-none transition-all"
              />
            </div>

            <div className="flex gap-4 w-full md:w-auto">
              <div className="flex items-center gap-2 bg-slate-50 px-3 py-1.5 border border-slate-200 rounded-xl w-1/3 md:w-auto">
                <Filter size={16} className="text-slate-400" />
                <select
                  value={directionFilter}
                  onChange={(e) => { setDirectionFilter(e.target.value); setPage(1); }}
                  className="bg-transparent text-sm text-slate-600 outline-none font-medium w-full"
                >
                  <option value="PENDING">Pendentes</option>
                  <option value="ROUTED">Enviados</option>
                  <option value="FAILED">Falhas</option>
                  <option value="ALL">Todos</option>
                </select>
              </div>

              <div className="flex items-center gap-2 bg-slate-50 px-3 py-1.5 border border-slate-200 rounded-xl w-1/3 md:w-auto">
                <Filter size={16} className="text-slate-400" />
                <select
                  value={dueDateFilter}
                  onChange={(e) => { setDueDateFilter(e.target.value); setPage(1); }}
                  className="bg-transparent text-sm text-slate-600 outline-none font-medium w-full"
                >
                  <option value="ALL">Vencimento (Todos)</option>
                  <option value="WITH_DUE">Com Vencimento</option>
                  <option value="NO_DUE">Sem Vencimento</option>
                </select>
              </div>

              <select
                value={docTypeFilter}
                onChange={(e) => { setDocTypeFilter(e.target.value); setPage(1); }}
                className="px-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-600 outline-none font-medium w-1/3 md:w-auto"
              >
                <option value="">Todos os Tipos</option>
                {contractsData?.map((c: any) => (
                  <option key={c.doc_type} value={c.doc_type}>{c.doc_type}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Main Table */}
          <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-slate-50/70 text-slate-400 text-xs font-bold uppercase border-b border-slate-100">
                    <th className="p-4 w-12 text-center">
                      <button onClick={toggleSelectAll} className="text-slate-400 hover:text-indigo-600 transition-colors">
                        {selectedIds.length === jobs.length && jobs.length > 0 ? (
                          <CheckSquare size={20} className="text-indigo-600" />
                        ) : (
                          <Square size={20} />
                        )}
                      </button>
                    </th>
                    <th className="p-4">Arquivo Anexo</th>
                    <th className="p-4">Dados do E-mail</th>
                    <th className="p-4">Vencimento (IA)</th>
                    <th className="p-4">Pasta Destino</th>
                    <th className="p-4">Status</th>
                    <th className="p-4 text-center">Ações</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-sm text-slate-700">
                  {isLoading || isFetching ? (
                    <tr>
                      <td colSpan={7} className="p-12 text-center">
                        <RefreshCcw className="animate-spin mx-auto text-indigo-500 mb-2" size={32} />
                        <span className="text-slate-400">Carregando dados...</span>
                      </td>
                    </tr>
                  ) : jobs.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="p-12 text-center text-slate-400">
                        <FileText className="mx-auto mb-3 opacity-20" size={48} />
                        Nenhum documento encontrado para este status.
                      </td>
                    </tr>
                  ) : (
                    jobs.map((job) => {
                      const isSelected = selectedIds.includes(job.id);
                      const isPending = job.direction_status === 'PENDING';
                      const isRouted = job.direction_status === 'ROUTED';
                      const isInspected = inspectedJob?.id === job.id;

                      return (
                        <tr 
                          key={job.id} 
                          className={`hover:bg-slate-50/50 transition-colors ${
                            isSelected ? 'bg-indigo-50/20' : ''
                          } ${isInspected ? 'bg-slate-50 border-l-4 border-l-indigo-600' : ''}`}
                        >
                          <td className="p-4 text-center">
                            <button 
                              onClick={() => toggleSelect(job.id)}
                              className="text-slate-400 hover:text-indigo-600 transition-colors"
                            >
                              {isSelected ? (
                                <CheckSquare size={20} className="text-indigo-600" />
                              ) : (
                                <Square size={20} />
                              )}
                            </button>
                          </td>

                          <td className="p-4">
                            <div className="flex items-center gap-3">
                              <div className="p-2 bg-indigo-50 rounded-lg text-indigo-600 shrink-0">
                                <FileText size={18} />
                              </div>
                              <div className="min-w-0">
                                <span className="font-semibold text-slate-800 block truncate max-w-[140px]" title={job.attachment_name}>
                                  {job.attachment_name}
                                </span>
                                <span className="text-[10px] uppercase font-bold text-slate-400 block tracking-wider">
                                  {job.doc_type || 'NÃO MAPEADO'}
                                </span>
                              </div>
                            </div>
                          </td>

                          <td className="p-4">
                            <div className="min-w-0">
                              <span className="font-semibold text-slate-800 block truncate max-w-[160px]" title={job.subject}>
                                {job.subject}
                              </span>
                              <span className="text-[10px] text-slate-400 block truncate max-w-[140px]" title={job.sender}>
                                De: {job.sender}
                              </span>
                            </div>
                          </td>

                          <td className="p-4">
                            <span className={`font-mono px-2 py-1 rounded-md text-xs font-semibold ${
                              job.original_due_date || job.email_body_due_date
                                ? 'bg-indigo-50 text-indigo-700'
                                : 'bg-slate-100 text-slate-600'
                            }`}>
                              {getReferenceDate(job)}
                            </span>
                          </td>

                          <td className="p-4">
                            {isRouted ? (
                              <div className="flex items-center gap-1.5 text-xs text-slate-500">
                                <span className="truncate max-w-[120px]" title={job.routed_path || ''}>
                                  {job.routed_path?.split('\\').pop() || 'servidor_pagamentos'}
                                </span>
                                <a 
                                  href="#" 
                                  onClick={(e) => { e.preventDefault(); alert(`Caminho completo:\n${job.routed_path}`); }}
                                  title="Ver caminho completo"
                                  className="text-indigo-500 hover:text-indigo-700"
                                >
                                  <ExternalLink size={12} />
                                </a>
                              </div>
                            ) : job.target_payment_date ? (
                              <span className="font-semibold text-indigo-600 text-xs">
                                Dia {job.target_payment_date.split('-')[2]}
                              </span>
                            ) : (
                              <span className="text-slate-400 text-xs italic">Aguardando calculo</span>
                            )}
                          </td>

                          <td className="p-4">
                            <span className={`inline-flex items-center gap-1.5 text-[10px] font-extrabold uppercase tracking-wider px-2 py-0.5 rounded-full ${
                              isRouted ? 'bg-emerald-100 text-emerald-700' :
                              isPending ? 'bg-amber-100 text-amber-700' :
                              'bg-rose-100 text-rose-700'
                            }`}>
                              {isRouted ? 'Roteado' : isPending ? 'Pendente' : 'Falhou'}
                            </span>
                          </td>

                          <td className="p-4">
                            <div className="flex justify-center gap-2 items-center">
                              <button
                                onClick={() => handleInspect(job)}
                                className={`px-2.5 py-1 rounded-lg text-xs font-bold border transition-colors ${
                                  isInspected 
                                    ? 'bg-slate-900 text-white border-slate-900' 
                                    : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-50 shadow-sm'
                                }`}
                              >
                                {isInspected ? 'Fechar' : 'Auditar'}
                              </button>

                              {isPending && !isInspected && (
                                <button
                                  onClick={() => handleRouteSingle(job.id)}
                                  disabled={routeMutation.isPending}
                                  className="bg-indigo-600 hover:bg-indigo-700 text-white px-2.5 py-1 rounded-lg text-xs font-bold shadow-sm transition-colors"
                                >
                                  Rotear
                                </button>
                              )}
                            </div>
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>

            {/* Pagination Footer */}
            {totalPages > 1 && (
              <div className="bg-slate-50/50 border-t border-slate-100 px-6 py-4 flex items-center justify-between">
                <span className="text-xs text-slate-400">
                  Mostrando {jobs.length} de {total} itens
                </span>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setPage(p => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="p-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-600 disabled:opacity-40 transition-colors"
                  >
                    <ChevronLeft size={16} />
                  </button>
                  <span className="text-xs font-semibold text-slate-700">
                    Página {page} de {totalPages}
                  </span>
                  <button
                    onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                    disabled={page === totalPages}
                    className="p-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-600 disabled:opacity-40 transition-colors"
                  >
                    <ChevronRight size={16} />
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Lado Direito: Gaveta Lateral de Inspeção e Auditoria (Split View) */}
        {inspectedJob && (
          <div className="w-full lg:w-[45%] bg-white rounded-2xl border border-slate-200 shadow-xl p-6 flex flex-col sticky top-8 h-[calc(100vh-6rem)] max-h-[calc(100vh-6rem)] z-10">
            {/* Cabeçalho */}
            <div className="flex items-center justify-between border-b border-slate-100 pb-4 shrink-0">
              <div>
                <h3 className="font-bold text-slate-800 text-lg truncate max-w-[280px]" title={inspectedJob.attachment_name}>
                  {inspectedJob.attachment_name}
                </h3>
                <span className="text-xs uppercase font-extrabold text-indigo-600 tracking-wider">
                  {inspectedJob.doc_type || 'Tipo não classificado'}
                </span>
              </div>
              <button 
                onClick={() => { setInspectedJob(null); setEmailContext(null); setFileUrl(''); }}
                className="text-slate-400 hover:text-slate-600 p-1.5 hover:bg-slate-100 rounded-lg transition-colors"
              >
                ✕
              </button>
            </div>

            {/* Área de Conteúdo com Scroll */}
            <div className="flex-1 overflow-y-auto pr-1 my-4 space-y-6">
              {/* Auditoria de Vencimento Inteligente por IA */}
              <div className="bg-gradient-to-br from-indigo-50 to-indigo-100/30 rounded-2xl border border-indigo-100 p-5 space-y-3.5 shadow-sm">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-extrabold text-indigo-500 uppercase tracking-wider block">Vencimento Consolidado</span>
                  <span className={`text-[9px] font-extrabold uppercase px-2.5 py-0.5 rounded-full ${
                    inspectedJob.detected_due_date && inspectedJob.due_date_source !== 'Data de Recebimento do E-mail (Fallback)'
                      ? 'bg-indigo-200 text-indigo-800' 
                      : 'bg-amber-100 text-amber-800 border border-amber-200'
                  }`}>
                    {inspectedJob.detected_due_date && inspectedJob.due_date_source !== 'Data de Recebimento do E-mail (Fallback)'
                      ? 'Vencimento Detectado' 
                      : 'Sem Vencimento'}
                  </span>
                </div>
                
                <div className="text-3xl font-black text-slate-900 tracking-tight">
                  {inspectedJob.detected_due_date ? (
                    (() => {
                      const parts = inspectedJob.detected_due_date.split('-');
                      if (parts.length === 3) return `${parts[2]}/${parts[1]}/${parts[0]}`;
                      return inspectedJob.detected_due_date;
                    })()
                  ) : 'Data Indisponível'}
                </div>

                <div className="text-xs font-semibold text-slate-700 bg-white/70 px-3 py-2 rounded-lg border border-indigo-100/50">
                  <span className="text-slate-400 block text-[10px] uppercase font-extrabold mb-0.5">Origem da Data Eleita:</span>
                  {inspectedJob.due_date_source || "Não calculado"}
                </div>

                <div className="bg-white border border-indigo-100/50 p-4 rounded-xl text-xs text-slate-700 leading-relaxed shadow-sm font-medium">
                  <span className="text-[10px] font-extrabold text-indigo-500 block mb-1.5 uppercase tracking-wider">Trecho Justificador (IA):</span>
                  {inspectedJob.due_date_context ? (
                    `"${inspectedJob.due_date_context}"`
                  ) : (
                    <span className="italic text-slate-400">Nenhum trecho de texto detectado. Usando data de recebimento do e-mail de fallback.</span>
                  )}
                </div>
              </div>

              {/* Visualizador de Arquivo Anexo */}
              <div className="space-y-2">
                <span className="text-xs font-extrabold text-slate-400 uppercase tracking-wider block">Visualizador do Anexo</span>
                {isFileLoading ? (
                  <div className="h-60 border border-slate-200 rounded-xl bg-slate-50 flex items-center justify-center text-slate-400 text-sm">
                    <RefreshCcw className="animate-spin text-indigo-500 mr-2" size={16} />
                    Buscando arquivo...
                  </div>
                ) : fileUrl ? (
                  inspectedJob.attachment_name?.toLowerCase().endsWith('.pdf') ? (
                    <iframe 
                      src={fileUrl} 
                      className="w-full h-80 border border-slate-200 rounded-xl shadow-sm bg-slate-100"
                      title="Visualizador de PDF"
                    />
                  ) : inspectedJob.attachment_name?.toLowerCase().match(/\.(jpg|jpeg|png|gif|webp)$/) ? (
                    <img 
                      src={fileUrl} 
                      className="w-full max-h-80 object-contain border border-slate-200 rounded-xl shadow-sm" 
                      alt="Visualizador de Imagem" 
                    />
                  ) : (
                    <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl text-slate-500 font-mono text-xs max-h-80 overflow-y-auto whitespace-pre-wrap">
                      {inspectedJob.extraction_result ? JSON.stringify(inspectedJob.extraction_result, null, 2) : "Sem conteúdo estruturado."}
                    </div>
                  )
                ) : (
                  <div className="h-60 border border-slate-200 rounded-xl bg-slate-50/50 flex items-center justify-center text-slate-400 text-xs italic">
                    Visualização indisponível.
                  </div>
                )}
              </div>

              {/* Corpo do E-mail */}
              <div className="space-y-2 flex flex-col min-h-0">
                <span className="text-xs font-extrabold text-slate-400 uppercase tracking-wider block">Corpo do E-mail</span>
                {isEmailLoading ? (
                  <div className="h-40 border border-slate-200 rounded-xl bg-slate-50 flex items-center justify-center text-slate-400 text-sm">
                    <RefreshCcw className="animate-spin text-indigo-500 mr-2" size={16} />
                    Buscando e-mail...
                  </div>
                ) : emailContext?.body_text ? (
                  <div className="p-4 bg-slate-900 border border-slate-950 rounded-xl text-slate-300 font-mono text-xs h-96 overflow-y-auto whitespace-pre-wrap leading-relaxed shadow-inner flex-shrink-0">
                    {emailContext.body_text}
                  </div>
                ) : (
                  <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl text-slate-400 text-xs italic">
                    Sem corpo de texto disponível.
                  </div>
                )}
              </div>
            </div>

            {/* Ações na Gaveta (Fixas no rodapé) */}
            {inspectedJob.direction_status === 'PENDING' && (
              <div className="border-t border-slate-100 pt-4 flex flex-col gap-3 shrink-0 bg-white">
                {customDateJobId === inspectedJob.id && (
                  <div className="flex items-center gap-2 bg-slate-50 border border-slate-200 rounded-xl p-2 shadow-sm w-full">
                    <input 
                      type="date" 
                      value={customDate}
                      onChange={e => setCustomDate(e.target.value)}
                      className="border border-slate-200 rounded-lg px-2.5 py-1.5 text-xs outline-none flex-1 font-semibold text-slate-700 bg-white"
                    />
                    <button
                      onClick={() => handleRouteCustom(inspectedJob.id)}
                      className="bg-emerald-600 text-white px-3.5 py-1.5 rounded-lg text-xs hover:bg-emerald-700 font-bold transition-colors"
                    >
                      Confirmar
                    </button>
                    <button
                      onClick={() => setCustomDateJobId(null)}
                      className="bg-slate-200 text-slate-700 px-3.5 py-1.5 rounded-lg text-xs hover:bg-slate-300 font-bold transition-colors"
                    >
                      Cancelar
                    </button>
                  </div>
                )}
                
                <div className="flex gap-3 w-full">
                  <button
                    onClick={() => handleRouteSingle(inspectedJob.id)}
                    disabled={routeMutation.isPending}
                    className="flex-1 bg-indigo-600 hover:bg-indigo-700 text-white py-2.5 rounded-xl font-bold transition-all text-sm shadow-md disabled:opacity-50"
                  >
                    {routeMutation.isPending ? 'Direcionando...' : 'Aprovar e Rotear'}
                  </button>
                  
                  <button
                    onClick={() => { setCustomDateJobId(inspectedJob.id); setCustomDate(''); }}
                    className="border border-slate-200 hover:bg-slate-50 text-slate-600 px-4 py-2.5 rounded-xl font-bold text-xs transition-colors shrink-0"
                  >
                    Data Manual
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
