# CHANGELOG - ELOS Sync

## [4.0.0] - 2026-06-16

### Adicionado
- **Roteamento Inteligente (V4.0)**:
  - Eleição da maior data de vencimento comparando anexos e o corpo do e-mail no `RoutingService`.
  - Fallback automático para a data de recebimento do e-mail quando nenhum vencimento for detectado.
  - Salvamento de metadados da eleição (origem da data de vencimento e contexto explicativo) no banco de dados para auditoria.
  - Criação da pasta de quarentena `"Sem Vencimento"` para arquivos sem prazo identificável.
  - Suporte ao parâmetro `destination_folder` customizável para os períodos configurados nas configurações de roteamento de pagamentos.
- **Frontend Split View**:
  - Tela de Direcionamento (`Routing.tsx`) reformulada com visualização lado a lado (esquerda: visualizador de anexos via Blob JWT; direita: gaveta de 45% com cabeçalho/rodapé fixos e scroll independente para auditoria e corpo do e-mail).
  - Filtros rápidos para visualização de itens "Com Vencimento" e "Sem Vencimento".
  - Seleção em lote para aprovação e roteamento de múltiplos e-mails simultâneos.

### Modificado
- **Banco de Dados**: Migração automática e segura no `init_db` para inclusão das colunas de vencimento, auditoria e quarentena de e-mails.
- **Parâmetros de Período**: Configuração de destino do período de vencimento permitindo diretórios arbitrários em vez do padrão `{ano-mes}/Dia_{payment_day}`.

## [3.0.0] - 2026-06-10

### Adicionado
- **Roteamento Financeiro Automatizado**: Nova funcionalidade no backend que calcula o dia do vencimento com base em 3 faixas programáveis de datas, direcionando arquivos para pastas como `ANO-MES/Dia_Z` no servidor de arquivos.
- **Precedência de Boleto**: Lógica que prioriza a data de vencimento do Boleto para a definição do dia de pagamento de todos os anexos do mesmo e-mail.
- **Interface de Roteamento**: Nova página de gerenciamento no frontend (`/routing`) exibindo arquivos pendentes e roteados com estatísticas e execução de envios manuais ou em lote.
- **Configurações de Roteamento**: Integração de configurações dinâmicas de intervalos de vencimento e caminhos de rede na página de Configurações Base.

### Modificado
- **Agrupamento de E-mails na Análise**: Modificado endpoint e UI para unificar e-mails no painel Outlook Style. Adicionado sub-seletor de anexos no painel de visualização e extração para múltiplos anexos por e-mail.
- **Filtro Inteligente de Ingestão**: Atualização na ingestão para descartar automaticamente imagens de assinatura leves (< 15 KB) ou com nomes comuns de assinatura.

### Segurança e Banco de Dados
- **Migração Automática**: Implementação de script ad-hoc no `init_db` para injetar os campos de direcionamento financeiro no SQLite sem interrupção de dados existentes.
