import os
import fitz  # PyMuPDF
from openai import OpenAI
import re

# ==========================================
# Configurações Iniciais e System Prompt
# ==========================================

SYSTEM_PROMPT = """Você é um Auditor Editorial Sênior de Periódicos Qualis A1.
Sua função é revisar rigorosamente textos acadêmicos para adequação estrita às normas ABNT aplicáveis no Brasil, além de garantir a excelência na redação científica.

Você analisará fragmentos de um artigo. Realize uma revisão focada nos seguintes pontos:
- Foco 1: Citações (NBR 10520) - Verifique o sistema autor-data. Aponte se citações diretas longas (mais de 3 linhas) precisam de recuo de 4cm, fonte menor e ausência de aspas.
- Foco 2: Referências (NBR 6023) - Caso encontre referências, confira os elementos essenciais (autor, título, edição, local, editora, data), uso correto do negrito/itálico e padronização.
- Foco 3: Estilo - Garanta a manutenção da voz impessoal (terceira pessoa), objetividade, clareza, coesão textual científica e gramática impecável da língua portuguesa.

Forneça um relatório apontando explicitamente:
1. O trecho com problema.
2. A regra ABNT ou de estilo violada.
3. A sugestão de correção.

Responda sempre em Markdown. Não reescreva o texto inteiro, foque nos problemas e soluções.
"""

def obter_cliente_openai():
    """Inicializa o cliente compatível com a API da DeepSeek."""
    # A API Key pode vir das variáveis de ambiente ou ser solicitada no início
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        api_key = input("🔑 Insira sua DEEPSEEK_API_KEY (ela não será salva, apenas usada nesta execução): ").strip()
        os.environ["DEEPSEEK_API_KEY"] = api_key
        
    try:
        # A API da DeepSeek é perfeitamente compatível com o formato da OpenAI
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )
        return client
    except Exception as e:
        print(f"❌ Erro ao inicializar cliente da API: {e}")
        return None

def extrair_texto_pdf(caminho_pdf):
    """Extrai texto do PDF mantendo parágrafos básicos."""
    print(f"📄 Extraindo texto do arquivo: {caminho_pdf}...")
    texto_completo = ""
    try:
        with fitz.open(caminho_pdf) as doc:
            for pagina in doc:
                texto_completo += pagina.get_text("text") + "\n"
        return texto_completo
    except Exception as e:
        print(f"❌ Erro ao ler o arquivo PDF. Verifique se o caminho está correto ou se o arquivo não está corrompido. Detalhes: {e}")
        return None

def fragmentar_texto(texto, max_chars=4000):
    """
    Divide o texto em blocos menores (chunks) de acordo com parágrafos,
    evitando cortar frases ao meio e mitigando limites de tokens da API.
    """
    print("✂️ Fragmentando o texto em blocos para envio à API...")
    
    # Dividindo por quebras de linha que representam parágrafos
    paragrafos = re.split(r'\n\s*\n', texto)
    
    fragmentos = []
    fragmento_atual = ""
    
    for p in paragrafos:
        if len(fragmento_atual) + len(p) < max_chars:
            fragmento_atual += p + "\n\n"
        else:
            if fragmento_atual:
                fragmentos.append(fragmento_atual.strip())
            fragmento_atual = p + "\n\n"
            
    if fragmento_atual.strip():
        fragmentos.append(fragmento_atual.strip())
        
    return fragmentos

def revisar_com_deepseek(client, fragmentos):
    """Envia os fragmentos para o DeepSeek e consolida as respostas."""
    relatorio_final = "# 📝 Relatório de Revisão ABNT e Estilo Acadêmico\n\n"
    relatorio_final += "*Gerado automaticamente via DeepSeek API.*\n\n---\n\n"
    
    for i, fragmento in enumerate(fragmentos, start=1):
        print(f"🚀 Enviando fragmento {i}/{len(fragmentos)} para o DeepSeek...")
        try:
            response = client.chat.completions.create(
                model="deepseek-chat",  # Utilize 'deepseek-reasoner' caso tenha acesso ao modelo de raciocínio
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Por favor, revise o seguinte trecho:\n\n{fragmento}"}
                ],
                max_tokens=2048,
                temperature=0.1 # Temperatura baixa para resultados coerentes e padronizados
            )
            
            conteudo_resposta = response.choices[0].message.content
            
            relatorio_final += f"## 🔎 Análise - Parte {i}\n\n"
            relatorio_final += conteudo_resposta + "\n\n---\n\n"
            
        except Exception as e:
            msg_erro = f"❌ Erro ao processar o fragmento {i}: {e}"
            print(msg_erro)
            relatorio_final += f"## 🔎 Análise - Parte {i}\n\n**Falha na API:** Não foi possível analisar este trecho devido a um erro na API ({e}).\n\n---\n\n"
            
    return relatorio_final

def salvar_relatorio(relatorio, caminho_saida="relatorio_revisao.md"):
    """Salva o relatório final em Markdown."""
    try:
        with open(caminho_saida, 'w', encoding='utf-8') as f:
            f.write(relatorio)
        print(f"✅ Relatório salvo com sucesso em: {os.path.abspath(caminho_saida)}")
    except Exception as e:
        print(f"❌ Erro ao salvar o arquivo: {e}")

def main():
    print("=" * 50)
    print("🎓 COORDENADOR DE REVISÃO ACADÊMICA ABNT")
    print("=" * 50)
    
    caminho_pdf = input("\n📂 Arraste e solte o PDF aqui ou digite o caminho completo do arquivo: ").strip()
    
    # Remove aspas caso o usuário tenha colado o caminho copiando do Windows
    if caminho_pdf.startswith('"') and caminho_pdf.endswith('"'):
        caminho_pdf = caminho_pdf[1:-1]
        
    if not os.path.isfile(caminho_pdf) or not caminho_pdf.lower().endswith(".pdf"):
        print("❌ Arquivo inválido! Certifique-se de ser um arquivo PDF existente.")
        return
        
    cliente_api = obter_cliente_openai()
    if not cliente_api:
        return
        
    texto_extraido = extrair_texto_pdf(caminho_pdf)
    if not texto_extraido:
        return
        
    fragmentos = fragmentar_texto(texto_extraido, max_chars=4000)
    print(f"📊 O documento foi dividido em {len(fragmentos)} partes para processamento.")
    
    relatorio = revisar_com_deepseek(cliente_api, fragmentos)
    
    nome_padrao = f"Revisao_ABNT_{os.path.splitext(os.path.basename(caminho_pdf))[0]}.md"
    salvar_relatorio(relatorio, caminho_saida=nome_padrao)
    
    print("\n✨ Processo finalizado! Vá revisar seu relatório em Markdown.")

if __name__ == "__main__":
    main()
