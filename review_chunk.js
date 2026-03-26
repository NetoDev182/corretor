const SYSTEM_PROMPT = `Você é um Auditor Editorial Sênior de Periódicos Qualis A1.
Sua função é revisar rigorosamente este texto acadêmico e emitir um parecer apontando correções baseadas nas normas da ABNT e excelência de redação.

Foco da Revisão:
1. Citações (NBR 10520): Verifique o sistema autor-data e o recuo de 4cm para citações longas (mais de 3 linhas).
2. Referências (NBR 6023): Confira elementos essenciais (autor, título, edição, local, editora, data), uso correto de negrito/itálico e ordem alfabética.
3. Estilo e Coesão: Garanta a voz impessoal (terceira pessoa), objetividade, clareza e gramática impecável.

Indique apenas os problemas encontrados, a regra ABNT violada e a sugestão de correção. Responda em Markdown.`;

module.exports = async (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'POST') return res.status(405).json({ erro: 'Método não permitido.' });

  const { fragmento, api_key } = req.body;
  const chaveApi = api_key || process.env.DEEPSEEK_API_KEY;

  if (!fragmento) return res.status(400).json({ erro: 'Nenhum texto recebido.' });
  if (!chaveApi) return res.status(400).json({ erro: 'Chave da API DeepSeek não fornecida.' });

  try {
    const response = await fetch('https://api.deepseek.com/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${chaveApi}`
      },
      body: JSON.stringify({
        model: 'deepseek-chat',
        messages: [
          { role: 'system', content: SYSTEM_PROMPT },
          { role: 'user', content: `Por favor, revise o seguinte trecho:\n\n${fragmento}` }
        ],
        max_tokens: 2048,
        temperature: 0.1
      })
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error?.message || `Erro HTTP ${response.status} da API DeepSeek`);
    }

    const relatorio = data.choices?.[0]?.message?.content;
    if (!relatorio) throw new Error('Resposta vazia da API.');

    return res.status(200).json({ relatorio });

  } catch (e) {
    return res.status(500).json({ erro: `Erro na API DeepSeek: ${e.message}` });
  }
};
