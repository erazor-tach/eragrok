#!/usr/bin/env python3
"""
Script pour ajouter le système de navigation dans toutes les pages HTML
"""

import os
import re

# Pages à modifier
pages = [
    'index.html',
    'workout.html',
    'nutrition.html',
    'progres.html',
    'cycle.html',
    'settings.html'
]

nav_script = '  <script src="js/navigation.js"></script>\n'

web_dir = r'E:\Projet\GIT\C\Dev\web'

for page in pages:
    filepath = os.path.join(web_dir, page)
    
    if not os.path.exists(filepath):
        print(f"❌ {page} not found")
        continue
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Vérifier si le script est déjà présent
    if 'js/navigation.js' in content:
        print(f"✅ {page} - Navigation already present")
        continue
    
    # Ajouter le script avant </body>
    if '</body>' in content:
        content = content.replace('</body>', nav_script + '</body>')
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ {page} - Navigation added")
    else:
        print(f"⚠️  {page} - No </body> tag found")

print("\n🎉 Done!")
