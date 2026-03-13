# Task: Detalhamento Técnico Profundo (Migração e Correções)

Este documento contém o escopo técnico minucioso necessário para que um desenvolvedor Frontend (React) e Backend (FastAPI) corrija os gaps oriundos da migração do Streamlit.

---

## 1. 🛡️ Controle de Acesso e Perfis Técnicos (RBAC)

**Backend (FastAPI - Segurança das Rotas)**
- Arquivos afetados: `app/api/v1/endpoints/contracts.py` e `app/api/v1/endpoints/settings.py`.
- **Ação:** Revisar as dependências `@router.get("")` de contratos para validar se apenas administradores devem ver/listar. Certificar-se de que os métodos de escrita (`POST`, `PUT`, `DELETE` e `PATCH`) usem estritamente `Depends(get_admin_user)`.
- **Ação Extra:** No endpoint de relatórios `export` (em `reports.py`), garantir que as permissões estejam corretas de acordo com a exigência corporativa.

**Frontend (React/Vite - Navegação)**
- Arquivos afetados: `src/components/Sidebar.tsx`, `src/App.tsx`.
- **Ação:** Ocultar definitivamente o botão **"Auditoria e Dados"** apagando a respectiva rota e desvinculando `src/pages/Audit.tsx` da aplicação.
- **Ação:** Nas rotas lógicas do React (`react-router-dom`), envolver `<Contracts />` e `<Settings />` em um `<ProtectedRoute requireAdmin={true} />` utilizando os dados de perfil (role: 'admin') do Zustand (`useAuthStore`).

---

## 2. 📊 Adequação do Dashboard (Painel Geral)

**Frontend (React/Vite)**
- Arquivo afetado: `src/pages/Dashboard.tsx`
- **Ação:** Exclusão da UI de Trust Score para o usuário base. Importar a role do usuário usando o `useAuthStore` e condicionalmente esconder a marcação da barra de Confiança.
```tsx
const isAdmin = useAuthStore(state => state.user?.role === 'admin');
// Na renderização condicional do TH e do TD:
{isAdmin && <th className="py-4 px-6 font-semibold">Confiança</th>}
{isAdmin && <td className="py-4 px-6"> ... UI da barra verde/amarela ... </td>}
```
- **Ação:** Para os casos de exibição de status, reforçar que `simplified_status === 'Não mapeado'` no backend reflita apropriadamente na etiqueta amarela na coluna status.

---

## 3. 📧 Visualização e Tratamento de E-mail (Texto UTF-8)

**Backend (Tratamento de Encoding - FastAPI)**
- Arquivos: `app/api/v1/endpoints/jobs.py`
- Os utilitários `decode_mime` foram implementados, porém os dados antigos corrompidos no SQLite (ou base configurada) persistem para corpos de e-mail mal formados.
- **Ação:** No momento em que o email é extraído (via `IngestionService` em `app/ingest/service.py`), forçar o casting para UTF-8 de `body_text`. Caso ocorram caracteres quebrados, adotar chardet ou ignore no byte decode nativo.

**Frontend (Visualização Humanizada)**
- Arquivo: `src/pages/Analysis.tsx`
- **Ação:** Substituir a renderização raw `<div className="whitespace-pre-wrap">{emailContext?.body_text}</div>` por uma abordagem rica. Caso o backend traga tags HTML parciais, deve-se sanitizar e renderizar visualmente:
```tsx
import DOMPurify from 'dompurify';
// ... e no render:
<div 
  className="prose prose-sm max-w-none text-slate-700 bg-white p-6 rounded border font-sans"
  dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(emailContext?.body_text) }}
/>
```

---

## 4. ⚙️ Agendamento Avançado e Execução Manual

**Frontend (Remoção do Prompt Feio)**
- Arquivo: `src/pages/Schedule.tsx`
- **Ação:** O clique em `Ingestão Manual` roda JavaScript `prompt()`. Isso é inaceitável em produção. Subistituir por um Modal (Dialog) customizado em Tailwind que pede:
  1. Input do tipo `date` para Data Início.
  2. Input do tipo `date` para Data Fim.
  3. Botões: `[Cancelar]` `[Confirmar Processamento]`.
Esses passagens de argumentos cairão como JSON padrão na chamada à API `/api/v1/pipeline/ingest/`.

**Backend (Cálculo Automático de Ranges de Backup)**
- Arquivo: `app/scheduler/tasks.py` (ou onde o loop de background dispara a rotina).
- **Ação:** Ajustar o "agendamento diário / semanal / quinzenal", alterando o fluxo para:
  Ao desencadear o cron, ele não manda "start e end em branco" gerando `None`. O código usará uma lógica `timedelta`: se o intervalo de ciclo é de 24h, o fetcher busca explicitamente do `(datetime.now() - timedelta(days=1))`. Sem isso, o IMAP varrerá infinitamente todo o Outlook gerando timeouts severos.

---

## 5. 🗄️ Tela "Dados dos e-mails" ou Repaginação do Histórico

**Frontend (Ponte e Construção de View Nova)**
- Uma das reclamação é a formatação em Excel e a tela para visualização de dados extraídos.
- **Ação:** Mover a funcionalidade de "Exportar" que hoje existe simples no `Dashboard.tsx` para uma ABA de exportação minuciosa ou tela separada `ExportPanel.tsx`.
- **Ação Frontend:** Implementar um Modal/Drawer para o Export, onde o usuário escolhe se exporta apenas dados padrão (ID, Assunto) ou a tabulação completa combinada com a Extração Dinâmica do LLM.
- **Ação Backend (`reports.py`):** O `job.extraction_result` extrai strings e booleans, porém se um contrato tem JSON encadeado recursivo (ex: `items: [...]`), ele não é exportado em formato liso para `.xlsx`. Precisamos adicionar o `pd.json_normalize` no pipeline ou nivelamento da árvore pro DataFrame (Flatten JSON method).

---

## 6. 🛠️ Configurações Globais (Recuperação vs Streamlit)

A ausência do array list de arquivos comissionados (`.pdf`, etc).

**Frontend (`Settings.tsx`)**
- Adicionar uma seção extra dedicada à chave `allowed_extensions`.
- A API `/v1/settings` deve lidar com arrays JSON.
- Criar a UI:
```tsx
const extSetting = settings.find(s => s.key === 'allowed_extensions')
const [extensions, setExtensions] = useState(extSetting ? extSetting.value.join(', ') : '.pdf');

// Ao salvar o form de extensões:
saveMutation.mutate({
  key: 'allowed_extensions',
  value: extensions.split(',').map(e => e.trim()),
  description: 'Extensões permitidas'
})
```

---

## 7. 🚨 Gestão de Contratos (Regressão Crítica de Editor JSON)

O Streamlit tinha o `st.data_editor` dinâmico montado a partir dos schemas de Contract JSON. O React perdeu a definição estrutural deste objeto dinâmico:
```json
// Schema original que o React perdeu a formatação guiada no form:
fields: [
  { name: "nome_fornecedor", type: "string", description: "O campo na NF" }
]
```

**Frontend (`Contracts.tsx`)**
- **Ação (Crucial):** O objeto de estado `selectedContract` precisa permitir a visualização da listagem `fields: ContractField[]`.
- Instanciar uma tabela simples utilizando Tailwind onde cada linha exibe:
   - `<input type="text" value={field.name} />`
   - `<select value={field.type}><option>string</option><option>number</option></select>`
   - `<input type="text" value={field.description} />`
- Mapear a alteração para dentro de `selectedContract.fields` usando map indexado, bem como ter um botão "Adicionar Campo Metadado" com `selectedContract.fields.push(...)`. Sem isso o Front envia o payload quebrando do Back na conversão do Pydantic ou substituindo os metadados valiosos da IA por zero.
