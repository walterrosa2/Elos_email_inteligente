import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';
import { Clock, Calendar, Play, Save, CheckCircle, AlertTriangle, Activity, X } from 'lucide-react';
import { useState, useEffect } from 'react';

interface ScheduleConfig {
  enabled: boolean;
  interval_minutes: number;
  start_time: string;
  end_time: string;
  days_of_week: number[];
}

export function Schedule() {
  const queryClient = useQueryClient();
  const [config, setConfig] = useState<ScheduleConfig>({
    enabled: false,
    interval_minutes: 60,
    start_time: "08:00",
    end_time: "20:00",
    days_of_week: [0, 1, 2, 3, 4]
  });

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [manualStart, setManualStart] = useState("");
  const [manualEnd, setManualEnd] = useState("");

  const [isProcessModalOpen, setIsProcessModalOpen] = useState(false);
  const [processStart, setProcessStart] = useState("");
  const [processEnd, setProcessEnd] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ['schedule-config'],
    queryFn: async () => {
      const response = await api.get('/api/v1/jobs/schedule/config');
      return response.data;
    }
  });

  useEffect(() => {
    if (data) {
      setConfig(data);
    }
  }, [data]);

  const saveMutation = useMutation({
    mutationFn: async (newConfig: ScheduleConfig) => {
      await api.post('/api/v1/jobs/schedule/config', newConfig);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['schedule-config'] });
      alert('Configuração de agendamento salva!');
    }
  });

  const ingestMutation = useMutation({
    mutationFn: async (dateParams?: { start_date?: string, end_date?: string }) => {
      await api.post('/api/v1/pipeline/ingest', dateParams || {});
    },
    onSuccess: () => {
       setIsModalOpen(false);
       setManualStart("");
       setManualEnd("");
       alert('Ingestão de e-mails disparada em background!');
    }
  });

  const processMutation = useMutation({
    mutationFn: async (dateParams?: { start_date?: string, end_date?: string }) => {
      await api.post('/api/v1/pipeline/process', dateParams || {});
    },
    onSuccess: () => {
       setIsProcessModalOpen(false);
       setProcessStart("");
       setProcessEnd("");
       alert('Processamento (OCR/IA) disparado em background!');
    }
  });

  const handleToggleDay = (day: number) => {
    setConfig(prev => {
      const days = prev.days_of_week.includes(day)
        ? prev.days_of_week.filter(d => d !== day)
        : [...prev.days_of_week, day];
      return { ...prev, days_of_week: days };
    });
  };

  if (isLoading) return <div className="p-8 text-center text-slate-500">Carregando agendador...</div>;

  const days = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom'];

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Agendamento de Ingestão</h1>
          <p className="text-slate-500 mt-1">Configure o intervalo automático de busca de e-mails.</p>
        </div>
        <div className="flex gap-4">
          <button 
            onClick={() => setIsModalOpen(true)}
            className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-3 rounded-xl font-bold transition-all shadow-lg shadow-indigo-200"
          >
            <Play size={20} fill="currentColor" />
            Ingestão Manual
          </button>
          <button 
            onClick={() => setIsProcessModalOpen(true)}
            className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white px-6 py-3 rounded-xl font-bold transition-all shadow-lg shadow-emerald-200"
          >
            <Activity size={20} />
            Processar Fila
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {/* Main Config */}
        <div className="md:col-span-2 space-y-6">
          <div className="bg-white p-8 rounded-2xl shadow-sm border border-slate-200">
            <div className="flex items-center justify-between mb-8">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-indigo-50 rounded-lg text-indigo-600">
                  <Clock size={24} />
                </div>
                <h3 className="text-xl font-bold text-slate-800">Parâmetros de Tempo</h3>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input 
                  type="checkbox" 
                  className="sr-only peer" 
                  checked={config.enabled}
                  onChange={(e) => setConfig({...config, enabled: e.target.checked})}
                />
                <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-indigo-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-indigo-600"></div>
                <span className="ml-3 text-sm font-bold text-slate-700">{config.enabled ? 'Ativado' : 'Desativado'}</span>
              </label>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-8">
              <div className="space-y-2">
                <label className="text-xs font-bold text-slate-400 uppercase tracking-widest pl-1">Janela de Início</label>
                <input 
                  type="time" 
                  value={config.start_time}
                  onChange={(e) => setConfig({...config, start_time: e.target.value})}
                  className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none text-slate-700 font-medium"
                />
              </div>
              <div className="space-y-2">
                <label className="text-xs font-bold text-slate-400 uppercase tracking-widest pl-1">Janela de Fim</label>
                <input 
                  type="time" 
                  value={config.end_time}
                  onChange={(e) => setConfig({...config, end_time: e.target.value})}
                  className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none text-slate-700 font-medium"
                />
              </div>
              <div className="space-y-2 sm:col-span-2">
                <label className="text-xs font-bold text-slate-400 uppercase tracking-widest pl-1">Intervalo (Minutos)</label>
                <select 
                  value={config.interval_minutes}
                  onChange={(e) => setConfig({...config, interval_minutes: parseInt(e.target.value)})}
                  className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none text-slate-700 font-medium"
                >
                  <option value={15}>15 minutos</option>
                  <option value={30}>30 minutos</option>
                  <option value={60}>1 hora</option>
                  <option value={120}>2 horas</option>
                  <option value={240}>4 horas</option>
                  <option value={720}>12 horas</option>
                </select>
              </div>
            </div>
          </div>

          <div className="bg-white p-8 rounded-2xl shadow-sm border border-slate-200">
            <div className="flex items-center gap-3 mb-8">
              <div className="p-2 bg-indigo-50 rounded-lg text-indigo-600">
                <Calendar size={24} />
              </div>
              <h3 className="text-xl font-bold text-slate-800">Dias da Semana</h3>
            </div>

            <div className="flex flex-wrap gap-3">
              {days.map((day, idx) => (
                <button
                  key={day}
                  onClick={() => handleToggleDay(idx)}
                  className={`flex-1 min-w-[60px] py-4 rounded-xl border font-bold transition-all ${
                    config.days_of_week.includes(idx)
                      ? 'bg-indigo-600 border-indigo-600 text-white shadow-md'
                      : 'bg-white border-slate-200 text-slate-400 hover:border-indigo-300 hover:text-indigo-600'
                  }`}
                >
                  {day}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Sidebar Status */}
        <div className="space-y-6">
          <div className="bg-indigo-900 text-white p-8 rounded-3xl shadow-xl shadow-indigo-200">
            <h4 className="flex items-center gap-2 text-indigo-200 font-bold text-xs uppercase tracking-widest mb-4">
              <CheckCircle size={14} />
              Status Atual
            </h4>
            <div className="space-y-6">
              <div>
                <p className="text-indigo-300 text-sm">Agendamento</p>
                <p className="text-2xl font-bold">{config.enabled ? 'Ativo' : 'Pausado'}</p>
              </div>
              <div>
                <p className="text-indigo-300 text-sm">Próxima Janela</p>
                <p className="text-lg font-semibold">{config.start_time} - {config.end_time}</p>
              </div>
              <button 
                onClick={() => saveMutation.mutate(config)}
                className="w-full bg-white text-indigo-900 py-4 rounded-xl font-bold hover:bg-indigo-50 transition-all flex items-center justify-center gap-2 mt-4"
              >
                <Save size={20} />
                {saveMutation.isPending ? 'Salvando...' : 'Salvar Alterações'}
              </button>
            </div>
          </div>

          <div className="bg-amber-50 border border-amber-100 p-6 rounded-2xl">
            <div className="flex items-start gap-3">
              <AlertTriangle className="text-amber-600 shrink-0" size={20} />
              <div>
                <h5 className="font-bold text-amber-800 text-sm">Nota sobre Agendamento</h5>
                <p className="text-xs text-amber-700 mt-1 leading-relaxed">
                  Esta configuração define apenas a intenção de execução. O serviço de background (Windows Service/Docker) deve estar rodando para processar estas regras.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Manual Ingestion Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-md overflow-hidden animate-in fade-in zoom-in-95 duration-200">
            <div className="p-6 border-b border-slate-100 flex justify-between items-center bg-slate-50/50">
              <h2 className="text-xl font-bold text-slate-800 flex items-center gap-2">
                <Play size={20} className="text-indigo-600" fill="currentColor" />
                Ingestão Manual (Busca)
              </h2>
              <button 
                onClick={() => setIsModalOpen(false)}
                className="text-slate-400 hover:text-slate-600 hover:bg-slate-100 p-2 rounded-lg transition-colors"
              >
                <X size={20} />
              </button>
            </div>
            
            <div className="p-6 space-y-5">
              <p className="text-sm text-slate-500 leading-relaxed">
                Baixa e-mails do servidor IMAP para a base local.
              </p>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">
                    Data Início (Opcional)
                  </label>
                  <input 
                    type="date" 
                    value={manualStart}
                    onChange={e => setManualStart(e.target.value)}
                    className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none transition-all text-slate-700"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">
                    Data Fim (Opcional)
                  </label>
                  <input 
                    type="date" 
                    value={manualEnd}
                    onChange={e => setManualEnd(e.target.value)}
                    className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none transition-all text-slate-700"
                  />
                </div>
              </div>
            </div>

            <div className="p-6 border-t border-slate-100 bg-slate-50/50 flex justify-end gap-3">
              <button 
                onClick={() => setIsModalOpen(false)}
                className="px-5 py-2.5 text-sm font-bold text-slate-600 hover:bg-slate-200 rounded-xl transition-colors"
              >
                Cancelar
              </button>
              <button 
                onClick={() => ingestMutation.mutate({ 
                  start_date: manualStart || undefined, 
                  end_date: manualEnd || undefined 
                })}
                disabled={ingestMutation.isPending}
                className="px-5 py-2.5 text-sm font-bold bg-indigo-600 text-white hover:bg-indigo-700 rounded-xl transition-colors shadow-md shadow-indigo-200 disabled:opacity-50 flex items-center gap-2"
              >
                {ingestMutation.isPending ? 'Iniciando...' : 'Confirmar Busca'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Manual Processing Modal */}
      {isProcessModalOpen && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-md overflow-hidden animate-in fade-in zoom-in-95 duration-200">
            <div className="p-6 border-b border-slate-100 flex justify-between items-center bg-slate-50/50">
              <h2 className="text-xl font-bold text-slate-800 flex items-center gap-2">
                <Activity size={20} className="text-emerald-600" />
                Processar Fila Pendente
              </h2>
              <button 
                onClick={() => setIsProcessModalOpen(false)}
                className="text-slate-400 hover:text-slate-600 hover:bg-slate-100 p-2 rounded-lg transition-colors"
              >
                <X size={20} />
              </button>
            </div>
            
            <div className="p-6 space-y-5">
              <p className="text-sm text-slate-500 leading-relaxed">
                Executa OCR e Extração de IA nos e-mails já baixados que estão aguardando processamento.
              </p>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">
                    De (Emails recebidos após)
                  </label>
                  <input 
                    type="date" 
                    value={processStart}
                    onChange={e => setProcessStart(e.target.value)}
                    className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-emerald-500 outline-none transition-all text-slate-700"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">
                    Até (Emails recebidos antes de)
                  </label>
                  <input 
                    type="date" 
                    value={processEnd}
                    onChange={e => setProcessEnd(e.target.value)}
                    className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-emerald-500 outline-none transition-all text-slate-700"
                  />
                </div>
              </div>
            </div>

            <div className="p-6 border-t border-slate-100 bg-slate-50/50 flex justify-end gap-3">
              <button 
                onClick={() => setIsProcessModalOpen(false)}
                className="px-5 py-2.5 text-sm font-bold text-slate-600 hover:bg-slate-200 rounded-xl transition-colors"
              >
                Cancelar
              </button>
              <button 
                onClick={() => processMutation.mutate({ 
                  start_date: processStart || undefined, 
                  end_date: processEnd || undefined 
                })}
                disabled={processMutation.isPending}
                className="px-5 py-2.5 text-sm font-bold bg-emerald-600 text-white hover:bg-emerald-700 rounded-xl transition-colors shadow-md shadow-emerald-200 disabled:opacity-50 flex items-center gap-2"
              >
                {processMutation.isPending ? 'Iniciando...' : 'Processar Agora'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
