# Serein Content API

Backend Python que gera práticas curtas de relaxamento sem expor a chave da OpenAI ao aplicativo Flutter.

## Executar localmente

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
# Edite .env e defina OPENAI_API_KEY
.venv/bin/python app.py
```

O serviço fica em `http://localhost:8080`. No emulador Android, o Flutter acessa o computador anfitrião em `http://10.0.2.2:8080`.

## Produção

Coloque o serviço atrás de HTTPS e autenticação de utilizador, restrinja `ALLOWED_ORIGINS`, substitua o limite local por Redis e nunca guarde `OPENAI_API_KEY` no APK ou em controlo de versão.
