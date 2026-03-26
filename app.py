# Entrypoint principal para a Vercel
# A Vercel detecta automaticamente este arquivo como o ponto de entrada Flask
from api.index import app

if __name__ == '__main__':
    app.run(debug=True, port=3000)
