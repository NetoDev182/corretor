const formidable = require('formidable');
const fs = require('fs');

// IMPORTANTE: Importar assim evita bug do pdf-parse em ambientes serverless
// que tenta carregar arquivos de teste com __dirname e crasha silenciosamente
const pdfParse = require('pdf-parse/lib/pdf-parse');

const handler = async (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'POST') return res.status(405).json({ erro: 'Método não permitido.' });

  try {
    const form = formidable({ maxFileSize: 30 * 1024 * 1024 });
    const [, files] = await form.parse(req);

    const pdfFile = Array.isArray(files.pdf) ? files.pdf[0] : files.pdf;
    if (!pdfFile) {
      return res.status(400).json({ erro: 'Nenhum arquivo PDF encontrado no envio.' });
    }

    const buffer = fs.readFileSync(pdfFile.filepath);
    const data = await pdfParse(buffer);
    const texto = data.text;

    if (!texto || texto.trim().length === 0) {
      return res.status(422).json({ erro: 'PDF sem texto extraível. Pode ser uma imagem escaneada.' });
    }

    // Fragmentação inteligente por parágrafos (~4000 caracteres por bloco)
    const paragrafos = texto.split(/\n\s*\n/);
    const fragmentos = [];
    let atual = '';

    for (const p of paragrafos) {
      if ((atual + p).length < 4000) {
        atual += p + '\n\n';
      } else {
        if (atual.trim()) fragmentos.push(atual.trim());
        atual = p + '\n\n';
      }
    }
    if (atual.trim()) fragmentos.push(atual.trim());

    return res.status(200).json({ fragmentos, totalPaginas: data.numpages });

  } catch (e) {
    console.error('Erro em /api/extract:', e);
    return res.status(500).json({ erro: `Erro interno: ${e.message}` });
  }
};

// Forma correta de desativar o bodyParser no Vercel para receber multipart/form-data
handler.config = {
  api: { bodyParser: false }
};

module.exports = handler;
