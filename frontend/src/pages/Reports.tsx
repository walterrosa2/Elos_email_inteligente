import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';
import { 
  Download, 
  Search, 
  Filter, 
  Calendar, 
  FileSpreadsheet, 
  Table as TableIcon,
  ChevronRight,
  Loader2
} from 'lucide-react';

interface Job {
  id: number;
  sender: string;
  subject: string;
  attachment_name: string;
  received_at: string;
  doc_type: string;
  status: string;
  simplified_status: string;
  extraction_result: Record<string, any> | null;
}

export function Reports() {
  const [statusFilter, setStatusFilter] = useState('');
  const [docTypeFilter, setDocTypeFilter] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [criticalityFilter, setCriticalityFilter] = useState('');
  const [filenameFilter, setFilenameFilter] = useState('');
  const [isExporting, setIsExporting] = useState(false);
  const [activeTab, setActiveTab] = useState('general');

  const { data, isLoading } = useQuery({
    queryKey: ['jobs-reports', statusFilter, docTypeFilter, startDate, endDate, searchTerm, criticalityFilter],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (statusFilter) params.append('status_filter', statusFilter);
      if (docTypeFilter) params.append('doc_type', docTypeFilter);
      if (startDate) params.append('start_date', startDate);
      if (endDate) params.append('end_date', endDate);
      if (searchTerm) params.append('subject', searchTerm);
      if (filenameFilter) params.append('filename', filenameFilter);
      if (criticalityFilter) params.append('criticality', criticalityFilter);
      params.append('limit', '200');
      
      const response = await api.get('/api/v1/jobs', { params });
      return response.data;
    }
  });

  const { data: contractsData } = useQuery({
    queryKey: ['contracts-list'],
    queryFn: async () => {
      const response = await api.get('/api/v1/contracts');
      return response.data;
    }
  });

  const jobs: Job[] = data?.items || [];
  
  // No longer deriving purely from loaded jobs, but from contracts list
  // Group jobs by doc_type for tabs
  const contractTypes = contractsData?.map((c: any) => c.doc_type) || [];

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

  const renderTable = (type: string) => {
    const filteredJobs = type === 'general' ? jobs : jobs.filter(j => j.doc_type === type);
    
    if (filteredJobs.length === 0) {
      return (
        <div className="p-12 text-center text-slate-400">
          <TableIcon className="mx-auto mb-4 opacity-10" size={64} />
          <p>Nenhum dado encontrado para esta categoria.</p>
        </div>
      );
    }

    if (type === 'general') {
      return (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold">
              <tr>
                <th className="py-3 px-4">ID</th>
                <th className="py-3 px-4">Data</th>
                <th className="py-3 px-4">Remetente</th>
                <th className="py-3 px-4">Assunto</th>
                <th className="py-3 px-4">Arquivo</th>
                <th className="py-3 px-4">Tipo</th>
                <th className="py-3 px-4">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredJobs.map(job => (
                <tr key={job.id} className="hover:bg-slate-50 transition-colors">
                  <td className="py-3 px-4 text-slate-500 font-mono text-xs">{job.id}</td>
                  <td className="py-3 px-4 text-slate-600">
                    {new Date(job.received_at).toLocaleDateString('pt-BR')}
                  </td>
                  <td className="py-3 px-4 text-slate-600 truncate max-w-[150px]">{job.sender}</td>
                  <td className="py-3 px-4 text-slate-600 truncate max-w-[200px]">{job.subject}</td>
                  <td className="py-3 px-4 text-slate-600 truncate max-w-[150px] font-medium">{job.attachment_name}</td>
                  <td className="py-3 px-4 italic text-slate-400">{job.doc_type}</td>
                  <td className="py-3 px-4">
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                      job.simplified_status === 'Concluído' ? 'bg-emerald-100 text-emerald-700' :
                      job.simplified_status === 'Não mapeado' ? 'bg-amber-100 text-amber-700' : 
                      'bg-rose-100 text-rose-700'
                    }`}>
                      {job.simplified_status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
    } else {
      // Dynamic columns based on extraction keys
      const allKeys = Array.from(new Set(filteredJobs.flatMap(j => Object.keys(j.extraction_result || {}))));
      
      return (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-indigo-50/50 border-b border-indigo-100 text-indigo-900 font-semibold">
              <tr>
                <th className="py-3 px-4 border-r border-indigo-100">Job ID</th>
                {allKeys.map(key => (
                  <th key={key} className="py-3 px-4 capitalize whitespace-nowrap">{key.replace(/_/g, ' ')}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredJobs.map(job => (
                <tr key={job.id} className="hover:bg-indigo-50/20 transition-colors">
                  <td className="py-3 px-4 border-r border-slate-100 text-slate-400 font-mono text-xs">{job.id}</td>
                  {allKeys.map(key => (
                    <td key={key} className="py-3 px-4 text-slate-600 whitespace-nowrap">
                      {String(job.extraction_result?.[key] || '-')}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
    }
  };

  return (
    <div className="p-8 max-w-[1600px] mx-auto animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 flex items-center gap-3 tracking-tight">
            <FileSpreadsheet className="text-indigo-600" size={32} />
            Relatórios Corporativos
          </h1>
          <p className="text-slate-500 mt-1">Geração de planilhas inteligentes e auditáveis com filtros avançados.</p>
        </div>
        
        <button 
          onClick={handleExport}
          disabled={isExporting}
          className="group relative flex items-center gap-3 bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-3 rounded-2xl font-bold transition-all shadow-xl shadow-indigo-100 disabled:opacity-50"
        >
          {isExporting ? <Loader2 className="animate-spin" size={20} /> : <Download size={20} className="group-hover:translate-y-0.5 transition-transform" />}
          {isExporting ? 'Processando Excel...' : 'Exportar para Excel'}
        </button>
      </div>

      {/* FILTERS PANEL */}
      <div className="bg-white p-6 rounded-3xl shadow-sm border border-slate-100 mb-8">
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-6">
          <div className="space-y-1.5">
            <label className="text-[10px] font-bold text-slate-400 uppercase tracking-widest ml-1">Busca Assunto</label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
              <input 
                type="text" 
                placeholder="Ex: Nota Fiscal..." 
                value={searchTerm}
                onChange={e => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-100 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none text-sm transition-all"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-[10px] font-bold text-slate-400 uppercase tracking-widest ml-1">Busca Anexo</label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
              <input 
                type="text" 
                placeholder="Ex: fatura.pdf..." 
                value={filenameFilter}
                onChange={e => setFilenameFilter(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-100 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none text-sm transition-all"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-[10px] font-bold text-slate-400 uppercase tracking-widest ml-1">Tipo Documento</label>
            <div className="relative">
              <Filter className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
              <select 
                value={docTypeFilter}
                onChange={e => setDocTypeFilter(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-100 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none text-sm appearance-none"
              >
                <option value="">Todos os Tipos</option>
                {contractsData?.map((c: any) => (
                  <option key={c.doc_type} value={c.doc_type}>{c.doc_type}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-[10px] font-bold text-slate-400 uppercase tracking-widest ml-1">Status</label>
            <select 
              value={statusFilter}
              onChange={e => setStatusFilter(e.target.value)}
              className="w-full px-4 py-2 bg-slate-50 border border-slate-100 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none text-sm"
            >
              <option value="">Todos Status</option>
              <option value="Concluído">Concluídos</option>
              <option value="Não mapeado">Não Mapeados</option>
              <option value="Erro">Com Erro</option>
            </select>
          </div>

          <div className="space-y-1.5">
            <label className="text-[10px] font-bold text-slate-400 uppercase tracking-widest ml-1">Criticidade</label>
            <select 
              value={criticalityFilter}
              onChange={e => setCriticalityFilter(e.target.value)}
              className="w-full px-4 py-2 bg-slate-50 border border-slate-100 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none text-sm"
            >
              <option value="">Todas</option>
              <option value="BAIXA">Baixa</option>
              <option value="MEDIA">Média</option>
              <option value="ALTA">Alta</option>
              <option value="CRITICA">Crítica</option>
            </select>
          </div>

          <div className="space-y-1.5 lg:col-span-2">
            <label className="text-[10px] font-bold text-slate-400 uppercase tracking-widest ml-1">Intervalo de Datas</label>
            <div className="flex items-center gap-3">
              <div className="relative flex-1">
                <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
                <input 
                  type="date" 
                  value={startDate}
                  onChange={e => setStartDate(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-100 rounded-xl text-sm outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
              <ChevronRight className="text-slate-300" size={16} />
              <div className="relative flex-1">
                <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
                <input 
                  type="date" 
                  value={endDate}
                  onChange={e => setEndDate(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-100 rounded-xl text-sm outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* PREVIEW TABS */}
      <div className="bg-white rounded-3xl shadow-xl shadow-slate-200/50 border border-slate-100 overflow-hidden flex flex-col min-h-[600px]">
        {/* Tab Headers */}
        <div className="flex border-b border-slate-100 px-4 bg-slate-50/30 overflow-x-auto styling-scrollbar">
          <button 
            onClick={() => setActiveTab('general')}
            className={`px-6 py-4 text-sm font-bold transition-all border-b-2 whitespace-nowrap ${
              activeTab === 'general' ? 'text-indigo-600 border-indigo-600 bg-white shadow-sm' : 'text-slate-400 border-transparent hover:text-slate-600'
            }`}
          >
            📊 Visão Geral (Emails)
          </button>
          {contractTypes.map((type: string) => (
            <button 
              key={type}
              onClick={() => setActiveTab(type)}
              className={`px-6 py-4 text-sm font-bold transition-all border-b-2 whitespace-nowrap ${
                activeTab === type ? 'text-indigo-600 border-indigo-600 bg-white shadow-sm' : 'text-slate-400 border-transparent hover:text-slate-600'
              }`}
            >
              📄 {type}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        <div className="flex-1 p-0 relative">
          {isLoading ? (
            <div className="absolute inset-0 flex flex-col items-center justify-center bg-white/80 z-20">
               <Loader2 className="animate-spin text-indigo-600 mb-4" size={48} />
               <p className="font-semibold text-slate-500">Minerando dados para preview...</p>
            </div>
          ) : (
            <div className="animate-in fade-in duration-300 h-full">
              {renderTable(activeTab)}
            </div>
          )}
        </div>
      </div>

      <div className="mt-6 flex items-center justify-between text-xs text-slate-400 font-medium px-4">
        <span>Mostrando até 200 registros filtrados para otimização de pré-visualização.</span>
        <span>A exportação final contemplará todos os registros do período.</span>
      </div>
    </div>
  );
}
