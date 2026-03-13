import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';
import { useAuthStore } from '../store/authStore';
import { Search, Filter, AlertCircle, CheckCircle, HelpCircle, Download, Calendar, CheckSquare, Square } from 'lucide-react';

interface JobSummary {
  id: number;
  status: string;
  simplified_status: 'Concluído' | 'Não mapeado' | 'Erro';
  sender: string;
  subject: string;
  attachment_name: string;
  received_at: string;
  doc_type: string | null;
  confidence: number | null;
  criticality: string | null;
}

export function Dashboard() {
  const queryClient = useQueryClient();
  const isAdmin = useAuthStore(state => state.user?.role === 'admin');
  const [statusFilter, setStatusFilter] = useState('');
  const [docTypeFilter, setDocTypeFilter] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [filenameFilter, setFilenameFilter] = useState('');
  const [criticalityFilter, setCriticalityFilter] = useState('');
  const [isExporting, setIsExporting] = useState(false);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);

  const handleExport = async () => {
    setIsExporting(true);
    try {
      const response = await api.get('/api/v1/reports/export', {
        responseType: 'blob',
        params: {
          status_filter: statusFilter || undefined,
          doc_type: docTypeFilter || undefined,
          start_date: startDate ? new Date(startDate).toISOString() : undefined,
          end_date: endDate ? new Date(endDate).toISOString() : undefined,
          subject: searchTerm || undefined,
          filename: filenameFilter || undefined,
          criticality: criticalityFilter || undefined
        }
      });
      
      const blob = new Blob([response.data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `Relatorio_ELOS_${new Date().toISOString().split('T')[0]}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to export report', error);
      alert('Erro ao exportar relatório.');
    } finally {
      setIsExporting(false);
    }
  };

  const { data, isLoading } = useQuery({
    queryKey: ['jobs', statusFilter, docTypeFilter, startDate, endDate, searchTerm, filenameFilter, criticalityFilter],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (statusFilter) params.append('status_filter', statusFilter);
      if (docTypeFilter) params.append('doc_type', docTypeFilter);
      if (startDate) params.append('start_date', startDate);
      if (endDate) params.append('end_date', endDate);
      if (searchTerm) params.append('subject', searchTerm);
      if (filenameFilter) params.append('filename', filenameFilter);
      if (criticalityFilter) params.append('criticality', criticalityFilter);
      
      const response = await api.get('/api/v1/jobs', { params });
      return response.data;
    }
  });

  const bulkApproveMutation = useMutation({
    mutationFn: async (ids: number[]) => {
      await api.post('/api/v1/jobs/bulk-approve', { ids });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
      setSelectedIds([]);
      alert('Documentos aprovados com sucesso!');
    }
  });

  const { data: contractsData } = useQuery({
    queryKey: ['contracts-list'],
    queryFn: async () => {
      const response = await api.get('/api/v1/contracts');
      return response.data;
    }
  });

  const jobs: JobSummary[] = data?.items || [];
  
  const stats = {
    concluidos: 0,
    nao_mapeados: 0,
    erros: 0
  };

  jobs.forEach(j => {
    if (j.simplified_status === 'Concluído') stats.concluidos++;
    if (j.simplified_status === 'Não mapeado') stats.nao_mapeados++;
    if (j.simplified_status === 'Erro') stats.erros++;
  });

  const toggleSelect = (id: number) => {
    setSelectedIds(prev => 
      prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]
    );
  };

  const toggleSelectAll = () => {
    if (selectedIds.length === jobs.length && jobs.length > 0) {
      setSelectedIds([]);
    } else {
      setSelectedIds(jobs.map(j => j.id));
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Visão Geral</h1>
          <p className="text-slate-500 mt-1">Acompanhe o status do processamento de e-mails e anexos.</p>
        </div>
        <div className="flex gap-4">
          {selectedIds.length > 0 && (
            <button 
              onClick={() => bulkApproveMutation.mutate(selectedIds)}
              className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-lg font-medium transition-colors shadow-sm animate-in fade-in slide-in-from-right-4"
            >
              <CheckCircle size={18} />
              Aprovar Selecionados ({selectedIds.length})
            </button>
          )}
          <button 
            onClick={handleExport}
            disabled={isExporting}
            className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg font-medium transition-colors shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isExporting ? <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div> : <Download size={18} />}
            {isExporting ? 'Exportando...' : 'Exportar Relatório'}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200 flex items-center gap-4 transition-all hover:shadow-md">
          <div className="h-12 w-12 rounded-full bg-emerald-100 flex items-center justify-center">
            <CheckCircle className="text-emerald-600" size={24} />
          </div>
          <div>
            <h3 className="text-slate-500 font-medium text-sm">Concluídos</h3>
            <p className="text-3xl font-bold text-slate-800">{stats.concluidos}</p>
          </div>
        </div>
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200 flex items-center gap-4 transition-all hover:shadow-md">
          <div className="h-12 w-12 rounded-full bg-amber-100 flex items-center justify-center">
            <HelpCircle className="text-amber-600" size={24} />
          </div>
          <div>
            <h3 className="text-slate-500 font-medium text-sm">Não Mapeados</h3>
            <p className="text-3xl font-bold text-slate-800">{stats.nao_mapeados}</p>
          </div>
        </div>
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200 flex items-center gap-4 transition-all hover:shadow-md">
           <div className="h-12 w-12 rounded-full bg-rose-100 flex items-center justify-center">
            <AlertCircle className="text-rose-600" size={24} />
          </div>
          <div>
            <h3 className="text-slate-500 font-medium text-sm">Com Erro</h3>
            <p className="text-3xl font-bold text-slate-800">{stats.erros}</p>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
        {/* Advanced Filters */}
        <div className="p-6 border-b border-slate-200 flex flex-col gap-4 bg-slate-50/50">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
              <input 
                type="text" 
                placeholder="Buscar assunto..." 
                value={searchTerm}
                onChange={e => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none text-sm"
              />
            </div>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
              <input 
                type="text" 
                placeholder="Buscar anexo..." 
                value={filenameFilter}
                onChange={e => setFilenameFilter(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none text-sm"
              />
            </div>
            <div className="flex items-center gap-2">
              <Filter size={16} className="text-slate-400" />
              <select 
                className="w-full border border-slate-300 rounded-lg px-3 py-2 bg-white text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                value={statusFilter}
                onChange={e => setStatusFilter(e.target.value)}
              >
                <option value="">Todos os Status</option>
                <option value="Concluído">Concluídos</option>
                <option value="Não mapeado">Não Mapeados</option>
                <option value="Erro">Com Erro</option>
              </select>
            </div>
            <div className="flex items-center gap-2">
              <Filter size={16} className="text-slate-400" />
              <select 
                className="w-full border border-slate-300 rounded-lg px-3 py-2 bg-white text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                value={criticalityFilter}
                onChange={e => setCriticalityFilter(e.target.value)}
              >
                <option value="">Criticidade (Todas)</option>
                <option value="BAIXA">Baixa</option>
                <option value="MEDIA">Média</option>
                <option value="ALTA">Alta</option>
                <option value="CRITICA">Crítica</option>
              </select>
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="flex items-center gap-2">
              <Filter size={16} className="text-slate-400" />
              <select 
                className="w-full border border-slate-300 rounded-lg px-3 py-2 bg-white text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                value={docTypeFilter}
                onChange={e => setDocTypeFilter(e.target.value)}
              >
                <option value="">Todos os Tipos de Documento</option>
                {contractsData?.map((c: any) => (
                  <option key={c.doc_type} value={c.doc_type}>{c.doc_type}</option>
                ))}
                <option value="UNKNOWN">Não Mapeado</option>
              </select>
            </div>
            <div className="flex items-center gap-2">
              <Calendar size={16} className="text-slate-400" />
              <input 
                type="date" 
                value={startDate}
                onChange={e => setStartDate(e.target.value)}
                className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
              />
            </div>
            <div className="flex items-center gap-2">
              <Calendar size={16} className="text-slate-400" />
              <input 
                type="date" 
                value={endDate}
                onChange={e => setEndDate(e.target.value)}
                className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
              />
            </div>
          </div>
        </div>

        <div className="overflow-x-auto">
          {isLoading ? (
            <div className="p-12 text-center text-slate-500 flex flex-col items-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mb-4"></div>
              <span>Carregando dados...</span>
            </div>
          ) : (
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50 text-slate-600 border-b border-slate-200 text-sm">
                  <th className="py-4 px-6 w-12">
                    <button onClick={toggleSelectAll} className="text-slate-400 hover:text-indigo-600 transition-colors">
                      {selectedIds.length === jobs.length && jobs.length > 0 ? <CheckSquare size={20} /> : <Square size={20} />}
                    </button>
                  </th>
                  <th className="py-4 px-6 font-semibold">Assunto do E-mail</th>
                  <th className="py-4 px-6 font-semibold">Arquivo / Criticidade</th>
                  <th className="py-4 px-6 font-semibold">Tipo</th>
                  {isAdmin && <th className="py-4 px-6 font-semibold">Confiança</th>}
                  <th className="py-4 px-6 font-semibold">Data</th>
                  <th className="py-4 px-6 font-semibold">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {jobs.length === 0 ? (
                  <tr><td colSpan={isAdmin ? 7 : 6} className="py-12 text-center text-slate-500">Nenhum registro encontrado.</td></tr>
                ) : (
                  jobs.map((job) => (
                    <tr key={job.id} className={`hover:bg-slate-50/80 transition-colors ${selectedIds.includes(job.id) ? 'bg-indigo-50/50' : ''}`}>
                      <td className="py-4 px-6">
                        <button onClick={() => toggleSelect(job.id)} className={`${selectedIds.includes(job.id) ? 'text-indigo-600' : 'text-slate-300 hover:text-slate-400'}`}>
                          {selectedIds.includes(job.id) ? <CheckSquare size={20} /> : <Square size={20} />}
                        </button>
                      </td>
                      <td className="py-4 px-6">
                        <div className="font-medium text-slate-800 truncate max-w-[250px]" title={job.subject}>{job.subject || '(Sem Assunto)'}</div>
                        <div className="text-xs text-slate-400 mt-1 truncate max-w-[250px]">{job.sender}</div>
                      </td>
                      <td className="py-4 px-6">
                        <div className="font-medium text-slate-800 truncate max-w-[250px]" title={job.attachment_name}>{job.attachment_name || '-'}</div>
                        {job.criticality && (
                           <span className={`mt-1 inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold ${
                             job.criticality === 'CRITICA' ? 'bg-rose-100 text-rose-700' :
                             job.criticality === 'ALTA' ? 'bg-orange-100 text-orange-700' :
                             job.criticality === 'MEDIA' ? 'bg-blue-100 text-blue-700' :
                             'bg-emerald-100 text-emerald-700'
                           }`}>
                             {job.criticality}
                           </span>
                        )}
                      </td>
                      <td className="py-4 px-6">
                        <span className="text-sm text-slate-600">{job.doc_type || '-'}</span>
                      </td>
                      {isAdmin && (
                        <td className="py-4 px-6">
                          <div className="flex items-center gap-2">
                             <div className={`h-1.5 w-12 rounded-full bg-slate-100 overflow-hidden`}>
                                <div 
                                  className={`h-full rounded-full ${
                                    (job.confidence || 0) > 80 ? 'bg-emerald-500' : 
                                    (job.confidence || 0) > 50 ? 'bg-amber-500' : 'bg-rose-500'
                                  }`}
                                  style={{ width: `${job.confidence || 0}%` }}
                                />
                             </div>
                             <span className="text-xs font-bold text-slate-500">{job.confidence || 0}%</span>
                          </div>
                        </td>
                      )}
                      <td className="py-4 px-6 text-slate-500 text-sm whitespace-nowrap">
                        {job.received_at ? new Date(job.received_at).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' }) : '-'}
                      </td>
                      <td className="py-4 px-6">
                        <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold border ${
                          job.simplified_status === 'Concluído' ? 'bg-emerald-50 text-emerald-700 border-emerald-200' :
                          job.simplified_status === 'Não mapeado' ? 'bg-amber-50 text-amber-700 border-amber-200' :
                          'bg-rose-50 text-rose-700 border-rose-200'
                        }`}>
                          {job.simplified_status}
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
