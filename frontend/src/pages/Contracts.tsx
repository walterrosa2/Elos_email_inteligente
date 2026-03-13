import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';
import { FileCode, Save, Plus, Trash2, TableProperties } from 'lucide-react';

interface ContractField {
  id?: number;
  name: string;
  description?: string;
  type: string;
  required: boolean;
}

interface Contract {
  doc_type: string;
  version: string;
  description: string;
  system_prompt: string;
  keywords: string[];
  fields?: ContractField[];
}

export function Contracts() {
  const queryClient = useQueryClient();
  const [selectedContract, setSelectedContract] = useState<Contract | null>(null);

  const { data: contracts, isLoading } = useQuery<Contract[]>({
    queryKey: ['contracts'],
    queryFn: async () => {
      const resp = await api.get('/api/v1/contracts');
      return resp.data;
    }
  });

  const saveMutation = useMutation({
    mutationFn: async (contract: Contract) => {
      await api.put(`/api/v1/contracts/${contract.doc_type}`, contract);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contracts'] });
      alert('Contrato atualizado com sucesso!');
    }
  });

  if (isLoading) {
    return <div className="p-8 text-slate-500">Carregando Contratos...</div>;
  }

  return (
    <div className="p-8 max-w-7xl mx-auto flex gap-8">
      
      {/* Sidebar List */}
      <div className="w-1/3 bg-white border border-slate-200 rounded-2xl shadow-sm flex flex-col">
        <div className="p-6 border-b border-slate-200 flex justify-between items-center bg-slate-50/50 rounded-t-2xl">
          <h2 className="text-xl font-bold text-slate-800">Contratos</h2>
          <button className="text-indigo-600 hover:bg-indigo-50 p-2 rounded-lg transition-colors">
            <Plus size={20} />
          </button>
        </div>
        <div className="p-4 flex flex-col gap-2 overflow-y-auto max-h-[600px]">
          {contracts?.map((c) => (
            <button
              key={c.doc_type}
              onClick={() => setSelectedContract(c)}
              className={`p-4 rounded-xl text-left border transition-all ${
                selectedContract?.doc_type === c.doc_type 
                  ? 'border-indigo-500 bg-indigo-50/50 shadow-sm' 
                  : 'border-slate-100 hover:border-slate-300 hover:bg-slate-50'
              }`}
            >
              <div className="font-semibold text-slate-800">{c.doc_type}</div>
              <div className="text-sm text-slate-500 truncate mt-1">{c.description}</div>
              <div className="mt-3 flex gap-2">
                <span className="text-xs bg-slate-100 text-slate-600 px-2 py-1 rounded-md">v{c.version}</span>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Editor */}
      <div className="w-2/3">
        {selectedContract ? (
          <div className="bg-white border border-slate-200 rounded-2xl shadow-sm">
            <div className="p-6 border-b border-slate-200 flex items-center gap-3 bg-slate-50/50 rounded-t-2xl">
              <div className="h-10 w-10 bg-indigo-100 text-indigo-700 rounded-lg flex items-center justify-center">
                <FileCode size={20} />
              </div>
              <h2 className="text-2xl font-bold text-slate-800">Editando: {selectedContract.doc_type}</h2>
            </div>
            
            <div className="p-6 space-y-6">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Descrição</label>
                <input 
                  type="text" 
                  value={selectedContract.description || ''}
                  onChange={e => setSelectedContract({...selectedContract, description: e.target.value})}
                  className="w-full border border-slate-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-indigo-500 outline-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Prompt IA (Instrução para LLM)</label>
                <textarea 
                  rows={6}
                  value={selectedContract.system_prompt || ''}
                  onChange={e => setSelectedContract({...selectedContract, system_prompt: e.target.value})}
                  className="w-full border border-slate-300 rounded-lg px-4 py-3 font-mono text-sm focus:ring-2 focus:ring-indigo-500 outline-none bg-slate-50"
                  placeholder="Instruções para a OpenAI..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Palavras Chave (Vírgula para separar)</label>
                <input 
                  type="text" 
                  value={selectedContract.keywords?.join(', ') || ''}
                  onChange={e => {
                    const keys = e.target.value.split(',').map(k => k.trim()).filter(Boolean);
                    setSelectedContract({...selectedContract, keywords: keys});
                  }}
                  className="w-full border border-slate-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-indigo-500 outline-none"
                />
              </div>

              {/* Dynamic Fields schema Editor */}
              <div className="pt-4 border-t border-slate-100">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <TableProperties size={18} className="text-slate-500" />
                    <label className="text-sm font-bold text-slate-700">Schema de Atributos para Extração da IA</label>
                  </div>
                  <button
                    onClick={() => {
                        const newFields = [...(selectedContract.fields || []), { name: '', description: '', type: 'string', required: false }];
                        setSelectedContract({...selectedContract, fields: newFields});
                    }}
                    className="flex items-center gap-1 text-xs bg-indigo-50 text-indigo-600 hover:bg-indigo-100 px-3 py-1.5 rounded-lg font-bold transition-colors"
                  >
                    <Plus size={14} /> Adicionar Campo
                  </button>
                </div>
                
                <div className="space-y-3">
                  {(selectedContract.fields || []).map((field, idx) => (
                    <div key={idx} className="flex gap-3 items-start bg-slate-50 p-3 rounded-xl border border-slate-200">
                       <div className="flex-1 space-y-3">
                          <div className="flex gap-3">
                              <input 
                                type="text"
                                placeholder="Nome do Campo (ex: valor_total)"
                                value={field.name}
                                onChange={e => {
                                  const updated = [...(selectedContract.fields || [])];
                                  updated[idx].name = e.target.value;
                                  setSelectedContract({...selectedContract, fields: updated});
                                }}
                                className="flex-1 border border-slate-300 rounded-lg px-3 py-1.5 text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                              />
                              <select
                                value={field.type}
                                onChange={e => {
                                  const updated = [...(selectedContract.fields || [])];
                                  updated[idx].type = e.target.value;
                                  setSelectedContract({...selectedContract, fields: updated});
                                }}
                                className="w-1/3 border border-slate-300 rounded-lg px-3 py-1.5 text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                              >
                                <option value="string">Texto (String)</option>
                                <option value="number">Número (Float/Int)</option>
                                <option value="boolean">Booleano</option>
                                <option value="date">Data (YYYY-MM-DD)</option>
                              </select>
                          </div>
                          <div className="flex gap-3 items-center">
                              <input 
                                type="text"
                                placeholder="Descrição / Dica para IA"
                                value={field.description || ''}
                                onChange={e => {
                                  const updated = [...(selectedContract.fields || [])];
                                  updated[idx].description = e.target.value;
                                  setSelectedContract({...selectedContract, fields: updated});
                                }}
                                className="flex-1 border border-slate-300 rounded-lg px-3 py-1.5 text-sm focus:ring-2 focus:ring-indigo-500 outline-none bg-white"
                              />
                              <label className="flex items-center gap-1.5 text-xs font-bold text-slate-600 cursor-pointer min-w-max">
                                <input 
                                  type="checkbox"
                                  checked={field.required}
                                  onChange={e => {
                                    const updated = [...(selectedContract.fields || [])];
                                    updated[idx].required = e.target.checked;
                                    setSelectedContract({...selectedContract, fields: updated});
                                  }}
                                  className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                                />
                                Obrigatório
                              </label>
                          </div>
                        </div>
                        <button 
                          onClick={() => {
                             const updated = (selectedContract.fields || []).filter((_, i) => i !== idx);
                             setSelectedContract({...selectedContract, fields: updated});
                          }}
                          className="text-rose-400 hover:text-rose-600 hover:bg-rose-50 p-2 rounded-lg transition-colors mt-1 shrink-0"
                          title="Remover campo"
                        >
                          <Trash2 size={16} />
                        </button>
                    </div>
                  ))}
                  {(!selectedContract.fields || selectedContract.fields.length === 0) && (
                    <div className="text-center py-6 text-slate-400 text-sm border-2 border-dashed border-slate-200 rounded-xl">
                      Nenhum atributo de extração configurado.<br/>
                      A IA retornará apenas um texto livre.
                    </div>
                  )}
                </div>
              </div>

              <div className="mt-8 flex justify-end gap-4 border-t border-slate-100 pt-6">
                <button 
                  className="flex items-center gap-2 px-6 py-2 border border-rose-200 text-rose-600 hover:bg-rose-50 rounded-lg transition-colors"
                >
                  <Trash2 size={18} />
                  Remover
                </button>
                <button 
                  onClick={() => saveMutation.mutate(selectedContract)}
                  disabled={saveMutation.isPending}
                  className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-2 rounded-lg font-medium transition-colors shadow-sm disabled:opacity-50"
                >
                  <Save size={18} />
                  {saveMutation.isPending ? 'Salvando...' : 'Salvar Alterações'}
                </button>
              </div>
            </div>
          </div>
        ) : (
          <div className="bg-white border border-slate-200 rounded-2xl shadow-sm h-full flex flex-col items-center justify-center text-slate-500 p-12">
            <FileCode size={48} className="text-slate-300 mb-4" />
            <h3 className="text-xl font-medium text-slate-700 mb-2">Nenhum contrato selecionado</h3>
            <p className="text-center max-w-sm">Selecione um contrato na lista ao lado para editar o seu mapeamento e prompt da IA.</p>
          </div>
        )}
      </div>
    </div>
  );
}
