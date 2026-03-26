const SYSTEM_PROMPT = `Você é um revisor ABNT objetivo e direto.

Analise o trecho e aponte no MÁXIMO 5 problemas reais. Ignore trechos sem problemas.

Para cada problema use este formato exato:
**Problema:** [trecho com erro]
**Regra:** [NBR violada ou estilo]
**Correção:** [como corrigir]

---

Foque apenas em: citações (NBR 10520), referências (NBR 6023) e voz impessoal. Seja breve.`;


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
