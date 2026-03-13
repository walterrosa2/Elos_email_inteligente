# Como Criar uma Senha de Aplicativo no Microsoft 365 (Outlook)

Se a sua conta de e-mail possui Autenticação de Fator Duplo (MFA/2FA) ativada, você precisará gerar uma **Senha de Aplicativo** para que o Python consiga acessar seus e-mails via IMAP. A senha normal da sua conta **não funcionará**.

## Passo a Passo

1.  **Acesse as Configurações de Segurança:**
    *   Vá para [https://mysignins.microsoft.com/security-info](https://mysignins.microsoft.com/security-info).
    *   Faça login com sua conta `Notafiscal@elos.org.br` e senha.

2.  **Adicionar Método de Entrada:**
    *   Na página "Informações de segurança", clique no botão **+ Adicionar método de entrada** (ou *+ Add sign-in method*).

3.  **Escolher Senha de Aplicativo:**
    *   No menu suspenso, escolha a opção **Senha de aplicativo** (App password).
    *   *Nota: Se essa opção não aparecer, pode ser que sua organização tenha bloqueado o uso de senhas de aplicativo. Nesse caso, contate o administrador de TI da ELOS.*

4.  **Criar a Senha:**
    *   Dê um nome para a senha, por exemplo: `PythonColetorNF`.
    *   Clique em **Avançar**.
    *   O sistema exibirá uma senha longa e aleatória (ex: `abcd efgh ijkl mnop`). **Copie essa senha**.

5.  **Atualizar o Projeto:**
    *   Abra o arquivo `.env` no seu projeto.
    *   Substitua a senha atual pela senha que você acabou de copiar no campo `EMAIL_PASSWORD`.
    
    ```env
    EMAIL_PASSWORD=sua_nova_senha_de_aplicativo_aqui
    ```

6.  **Testar:**
    *   Reinicie o aplicativo Streamlit e tente executar a coleta novamente.

---

### Observação Importante sobre IMAP no Exchange ("Basic Auth")

A Microsoft está desativando a "Autenticação Básica" (usuário/senha) para IMAP em muitos tenants. Se mesmo com a Senha de Aplicativo você receber erro de autenticação (`LOGIN failed`), pode ser necessário migrar a autenticação para **OAuth2 (Modern Auth)**.

Se isso ocorrer, o código precisará ser alterado para usar bibliotecas que suportem OAuth2 com Azure AD (como `MSAL` ou `O365`), mas tente primeiro com a Senha de Aplicativo.
