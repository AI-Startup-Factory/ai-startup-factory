import os
import requests
import re

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

def fetch_top_startups(limit=5):
    """Mengambil Top N startup dengan skor tertinggi."""
    url = f"{SUPABASE_URL}/rest/v1/ideas?select=*&startup_name=not.is.null&order=opportunity_score.desc&limit={limit}"
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        return r.json()
    return []

def slugify(text):
    """Mengubah nama startup menjadi format nama file yang aman (e.g., 'AI Factory' -> 'ai-factory')."""
    return re.sub(r'[\W_]+', '-', text.lower()).strip('-')

def generate_html(data):
    """Menyusun HTML menggunakan Tailwind CSS (Template Top 5)."""
    name = data.get("startup_name", "AI Startup")
    pitch = data.get("startup_pitch", "Innovative solution for modern problems.")
    features = data.get("mvp_spec", [])
    stack = data.get("tech_stack", [])
    problem = data.get("problem", "")
    score = data.get("opportunity_score", 0)

    features_html = "".join([f"<li class='mb-3 flex items-start'><span class='text-green-500 mr-2'>✔</span> {f}</li>" for f in features])
    stack_html = "".join([f"<span class='bg-indigo-100 text-indigo-700 text-xs font-bold mr-2 mb-2 px-3 py-1 rounded-full uppercase tracking-wider'>{s}</span>" for s in stack])

    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{name} | Visionary Startup</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-slate-50 text-slate-900 font-sans">
        <nav class="p-6 bg-white shadow-sm flex justify-between items-center">
            <span class="font-black text-2xl tracking-tighter text-indigo-600">{name.upper()}</span>
            <div class="bg-indigo-50 text-indigo-600 px-4 py-1 rounded-full text-sm font-bold">
                Opportunity Score: {score}/25
            </div>
        </nav>

        <header class="container mx-auto px-6 py-24 text-center">
            <h1 class="text-6xl font-extrabold text-slate-900 mb-6 tracking-tight">{name}</h1>
            <p class="text-2xl text-slate-600 mb-10 max-w-3xl mx-auto leading-relaxed">{pitch}</p>
            <div class="flex justify-center gap-4">
                <a href="#" class="bg-indigo-600 text-white px-10 py-4 rounded-xl font-bold text-lg hover:bg-indigo-700 shadow-lg shadow-indigo-200 transition-all">Launch MVP</a>
                <a href="#" class="bg-white border border-slate-200 text-slate-600 px-10 py-4 rounded-xl font-bold text-lg hover:bg-slate-50 transition-all">Learn More</a>
            </div>
        </header>

        <section class="container mx-auto px-6 py-20 border-t border-slate-200">
            <div class="grid lg:grid-cols-2 gap-20">
                <div>
                    <h2 class="text-sm font-black uppercase tracking-[0.2em] text-indigo-500 mb-4">The Challenge</h2>
                    <h3 class="text-4xl font-bold mb-6 text-slate-800">Why this matters now</h3>
                    <p class="text-xl text-slate-600 leading-relaxed italic border-l-4 border-indigo-200 pl-6">"{problem}"</p>
                </div>
                <div class="bg-white p-10 rounded-3xl shadow-xl shadow-slate-200/50 border border-slate-100">
                    <h2 class="text-2xl font-bold mb-8 flex items-center">
                        MVP Roadmap
                    </h2>
                    <ul class="text-lg text-slate-600 space-y-2">
                        {features_html}
                    </ul>
                </div>
            </div>
        </section>

        <section class="bg-slate-900 py-20 text-white text-center">
            <div class="container mx-auto px-6">
                <h2 class="text-sm font-black uppercase tracking-[0.2em] text-indigo-400 mb-8">Technical Foundation</h2>
                <div class="flex flex-wrap justify-center gap-3 max-w-2xl mx-auto">
                    {stack_html}
                </div>
            </div>
        </section>

        <footer class="py-12 bg-white text-center border-t border-slate-100">
            <p class="text-slate-400 font-medium tracking-wide italic">AI-Generated Blueprint &copy; 2026</p>
        </footer>
    </body>
    </html>
    """

def main():
    print("🚀 Fetching Top 5 Startup Blueprints...")
    startups = fetch_top_startups(5)
    
    if not startups:
        print("❌ No startup blueprints found in database.")
        return

    # Buat folder output jika belum ada
    output_dir = "dist"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for startup in startups:
        name = startup.get("startup_name", "Unknown")
        slug = slugify(name)
        print(f"📦 Generating: {name} ({slug}.html)")
        
        html_content = generate_html(startup)
        
        filepath = os.path.join(output_dir, f"{slug}.html")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_content)
    
    print(f"\n✅ Done! Check the '{output_dir}' folder for {len(startups)} landing pages.")

if __name__ == "__main__":
    main()
