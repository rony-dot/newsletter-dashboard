import { NextRequest, NextResponse } from 'next/server';
import { writeFile, mkdir } from 'fs/promises';
import { join } from 'path';
import { randomUUID } from 'crypto';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const imageBase64 = body.image as string;

    if (!imageBase64) {
      return NextResponse.json({ error: 'Imagem é obrigatória' }, { status: 400 });
    }

    // Remove data URL prefix if present
    const base64Data = imageBase64.replace(/^data:image\/\w+;base64,/, '');
    const buffer = Buffer.from(base64Data, 'base64');

    // Save to public directory
    const filename = `guru-card-${randomUUID()}.png`;
    const dir = join(process.cwd(), 'public', 'shares');

    await mkdir(dir, { recursive: true });
    await writeFile(join(dir, filename), buffer);

    // Return public URL
    const origin = request.headers.get('origin') || request.nextUrl.origin;
    const url = `${origin}/shares/${filename}`;

    return NextResponse.json({ url, filename });
  } catch (error) {
    console.error('Share API error:', error);
    return NextResponse.json(
      { error: 'Erro ao salvar imagem' },
      { status: 500 }
    );
  }
}
