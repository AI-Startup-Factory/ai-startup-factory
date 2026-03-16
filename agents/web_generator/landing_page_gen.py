import os
import re
# Import infrastruktur core
from core.config import settings
from core.database import db

def fetch_top_startups(limit=5):
    """Mengambil Top N startup berdasarkan opportunity_score tertinggi."""
    query = f"startup_name=not.is.null&order=opportunity_score.desc&limit={limit}&select=*"
    return db.fetch_records("ideas", query)

def slugify(text):
    """Mengubah nama startup menjadi format nama file yang aman."""
    return re.sub(r'[\W_]+', '-', text.lower()).strip('-')

def generate_html_template(data):
    """Menyusun HTML menggunakan Tailwind CSS."""
    name = data.get("startup_name", "AI Startup")
    pitch = data.get("startup_pitch", "Innovative solution for modern problems.")
    features = data.get("mvp_spec", [])
    stack = data.get("tech_stack", [])
    problem = data.get("problem", "")
    score = data.get("opportunity_score", 0)

    # Membangun komponen HTML secara dinamis
    features_html = "".join([
        f"<li class='mb-3 flex items-start text-slate-600'><span class='text-indigo-500 mr-3 mt-1 text-sm'>◆</span> {f}</li>" 
        for f in features
    ])
    
    stack_html = "".join([
        f"<span class='bg-slate-800 text-slate-300 text-[10px] font-black mr-2 mb-2 px-3 py-1 rounded border border-slate-700 uppercase tracking-widest'>{s}</span>" 
        for s in stack
    ])

    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{name} | Startup Concept</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;700;800&display=swap" rel="stylesheet">
        <style>body {{ font-family: 'Plus Jakarta Sans', sans-serif; }}</style>
    </head>
    <body class="bg-white text-slate-900 overflow-x-hidden">
        <nav class="p-8 flex justify-between items-center max-w-7xl mx-auto">
            <span class="font-extrabold text-xl tracking-tighter uppercase">{name}</span>
            <div class="px-4 py-1.5 border border-slate-200 rounded-full text-xs font-bold text-slate-500 uppercase tracking-widest">
                Potential: {score}/100
            </div>
        </nav>

        <main class="max-w-7xl mx-auto px-8">
            <header class="py-24 max-w-4xl">
                <h1 class="text-7xl font-extrabold tracking-tighter text-slate-900 mb-8 leading-[1.1]">{name}</h1>
                <p class="text-2xl text-slate-500 leading-relaxed font-medium mb-12">{pitch}</p>
                <div class="flex items-center gap-6">
                    <button class="bg-indigo-600 text-white px-8 py-4 rounded-full font-bold hover:bg-indigo-700 transition-all shadow-xl shadow-indigo-100">Contact Founders</button>
                    <button class="text-slate-900 font-bold border-b-2 border-slate-900 py-1">View Prototype</button>
                </div>
            </header>

            <section class="py-24 border-t border-slate-100">
                <div class="grid lg:grid-cols-12 gap-16">
                    <div class="lg:col-span-7">
                        <span class="text-indigo-600 font-bold uppercase tracking-[0.3em] text-[10px] mb-6 block">Origin Problem</span>
                        <blockquote class="text-3xl font-bold text-slate-800 leading-snug">
                            "{problem}"
                        </blockquote>
                    </div>
                    <div class="lg:col-span-5 bg-slate-50 p-12 rounded-[40px]">
                        <h3 class="font-extrabold text-xl mb-8 uppercase tracking-tighter">Initial Roadmap</h3>
                        <ul class="space-y-4 font-medium italic">
                            {features_html}
                        </ul>
                    </div>
                </div>
            </section>
        </main>

        <section class="bg-slate-950 py-32 text-white">
            <div class="max-w-7xl mx-auto px-8 flex flex-col items-center">
                <h2 class="text-[10px] font-black uppercase tracking-[0.4em] text-slate-500 mb-12">Built With</h2>
                <div class="flex flex-wrap justify-center gap-3">
                    {stack_html}
                </div>
            </div>
        </section>

        <footer class="py-12 text-center text-slate-400 text-[10px] font-bold uppercase tracking-widest">
            AI Startup Factory Blueprint &copy; 2026
        </footer>
    </body>
    </html>
    """

def main():
    print("🎨 [AGENT] Generating High-Priority Landing Pages...")
    
    # Ambil 5 startup terbaik
    startups = fetch_top_startups(5)
    
    if not startups:
        print("✅ No startups found to generate. Make sure blueprints are ready.")
        return

    # Pastikan direktori output 'dist' tersedia
    output_dir = "dist"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for startup in startups:
        name = startup.get("startup_name", "Unknown")
        slug = slugify(name)
        
        print(f"📦 Processing: {name} -> {output_dir}/{slug}.html")
        
        html_content = generate_html_template(startup)
        
        file_path = os.path.join(output_dir, f"{slug}.html")
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(html_content)
        except Exception as e:
            print(f"❌ Failed to write file: {e}")

    print(f"\n✨ Generation Finished! {len(startups)} landing pages are ready in '{output_dir}/'.")

if __name__ == "__main__":
    main()
