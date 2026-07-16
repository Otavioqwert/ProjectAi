import re
import sqlite3
from typing import List, Dict, Tuple

class RBMIndexer:
    def __init__(self, db_path: str = "memory.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Inicializa o banco de dados SQLite para tripletos RBM."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rbm_triplets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT NOT NULL,
                predicate TEXT NOT NULL,
                object TEXT NOT NULL,
                source_text TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_subject ON rbm_triplets(subject)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_predicate ON rbm_triplets(predicate)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_object ON rbm_triplets(object)')
        conn.commit()
        conn.close()

    def split_sentences(self, text: str) -> List[str]:
        """Divide texto em sentenças usando regex nativo."""
        # Padrão simples para dividir por pontuação final
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        return [s.strip() for s in sentences if s.strip()]

    def extract_triplets(self, sentence: str) -> List[Tuple[str, str, str]]:
        """Extrai tripletos (Sujeito, Predicado, Objeto) de uma sentença."""
        triplets = []
        
        # Padrões simples de extração
        # 1. "X é Y" / "X são Y"
        pattern_is = r'(.+?)\s+(?:é|são|era|eram|será|serão)\s+(.+)'
        match = re.search(pattern_is, sentence, re.IGNORECASE)
        if match:
            triplets.append((match.group(1).strip(), 'is', match.group(2).strip().rstrip('.')))

        # 2. "X tem Y" / "X possui Y"
        pattern_have = r'(.+?)\s+(?:tem|possui|havia|tinha)\s+(.+)'
        match = re.search(pattern_have, sentence, re.IGNORECASE)
        if match:
            triplets.append((match.group(1).strip(), 'have', match.group(2).strip().rstrip('.')))

        # 3. "X semelhante a Y" / "X igual a Y"
        pattern_similar = r'(.+?)\s+(?:semelhante a|igual a|como)\s+(.+)'
        match = re.search(pattern_similar, sentence, re.IGNORECASE)
        if match:
            triplets.append((match.group(1).strip(), '~~', match.group(2).strip().rstrip('.')))

        return triplets

    def index_text(self, text: str, source: str = "") -> int:
        """Indexa um texto completo, extraindo e salvando tripletos."""
        sentences = self.split_sentences(text)
        count = 0
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for sentence in sentences:
            triplets = self.extract_triplets(sentence)
            for subj, pred, obj in triplets:
                cursor.execute(
                    'INSERT INTO rbm_triplets (subject, predicate, object, source_text) VALUES (?, ?, ?, ?)',
                    (subj, pred, obj, source)
                )
                count += 1
        
        conn.commit()
        conn.close()
        return count

    def search_by_subject(self, subject: str) -> List[Dict]:
        """Busca tripletos por sujeito."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM rbm_triplets WHERE subject LIKE ?', (f'%{subject}%',))
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def search_by_keyword(self, keyword: str) -> List[Dict]:
        """Busca tripletos que contenham a palavra-chave em qualquer campo."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        query = f'%{keyword}%'
        cursor.execute('''
            SELECT * FROM rbm_triplets 
            WHERE subject LIKE ? OR predicate LIKE ? OR object LIKE ?
        ''', (query, query, query))
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def get_all_triplets(self) -> List[Dict]:
        """Retorna todos os tripletos armazenados."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM rbm_triplets ORDER BY created_at DESC')
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
