# # test_mongodb_setup.py
# from Backend.mongodb_client import MongoDBClient

# print("Testing MongoDB connection...")

# try:
#     client = MongoDBClient()
    
#     # Test 1: Check connection
#     client.client.admin.command('ping')
#     print("✅ MongoDB connection successful")
    
#     # Test 2: Check collection exists
#     db = client.client[client.db_name]
#     collections = db.list_collection_names()
#     print(f"✅ Available collections: {collections}")
    
#     if "module_vectors" in collections:
#         print("✅ module_vectors collection exists")
#     else:
#         print("⚠️ module_vectors collection not found - will be created on first insert")
    
#     # Test 3: Check indexes
#     print("\n📊 Checking indexes...")
#     indexes = list(client.collection.list_indexes())
    
#     for idx in indexes:
#         print(f"  - Index: {idx.get('name', 'N/A')}")
#         if 'vector_index' in idx.get('name', ''):
#             print("    ✅ Vector search index found!")
    
#     # Test 4: Check document count
#     count = client.collection.count_documents({})
#     print(f"\n📈 Current document count: {count}")
    
#     if count > 0:
#         print("⚠️ Collection has existing data - you may want to clear it first")
#         sample = client.collection.find_one()
#         print(f"Sample document keys: {list(sample.keys())}")
#     else:
#         print("✅ Collection is empty and ready for ingestion")
    
#     client.close()
#     print("\n✅ MongoDB setup verification complete!")
    
# except Exception as e:
#     print(f"❌ Error: {e}")


# # check_indexes.py
# from Backend.mongodb_client import MongoDBClient
# from dotenv import load_dotenv

# load_dotenv()
# client = MongoDBClient()

# print("All indexes in collection:")
# for idx in client.collection.list_indexes():
#     print(f"\nIndex name: {idx.get('name')}")
#     print(f"Keys: {idx.get('key', {})}")
#     if 'type' in idx:
#         print(f"Type: {idx.get('type')}")

# client.close()















# # check_kb_file.py
# import json

# kb_path = r"C:\Users\newbr\OneDrive\Desktop\AISHINEBE_CLAUDE\Parsed_Module1_KB.json"

# print(f"Checking file: {kb_path}")

# try:
#     with open(kb_path, 'r', encoding='utf-8') as f:
#         content = f.read()
#         print(f"✅ File size: {len(content)} bytes")
        
#         if len(content) == 0:
#             print("❌ File is EMPTY!")
#         elif len(content) < 100:
#             print(f"⚠️ File is very small. Contents:\n{content}")
#         else:
#             print(f"First 200 characters:\n{content[:200]}")
        
#         # Try to parse
#         f.seek(0)
#         data = json.load(f)
#         print(f"✅ Valid JSON with {len(data)} entries")
        
#         if len(data) > 0:
#             print(f"\nFirst entry:")
#             print(f"  Topic: {data[0].get('topic', 'N/A')}")
#             print(f"  Has content: {len(data[0].get('content', '')) > 0}")
            
# except FileNotFoundError:
#     print("❌ FILE NOT FOUND!")
# except json.JSONDecodeError as e:
#     print(f"❌ INVALID JSON: {e}")
# except Exception as e:
#     print(f"❌ ERROR: {e}")

















from pymongo import MongoClient
import os
from dotenv import load_dotenv
import json

load_dotenv()

client = MongoClient(os.getenv("MONGO_DB_URI"))
db = client[os.getenv("DB_NAME")]

print("="*60)
print("MONGODB STRUCTURE ANALYSIS")
print("="*60)

# Collection stats
coll = db["module_vectors"]
total = coll.count_documents({})
pres_count = coll.count_documents({"source": "presentation"})
kb_count = coll.count_documents({"source": "knowledge_base"})

print(f"\nTotal documents: {total}")
print(f"Presentation docs: {pres_count}")
print(f"KB docs: {kb_count}")

# Sample presentation doc
print("\n" + "="*60)
print("PRESENTATION SAMPLE")
print("="*60)
pres = coll.find_one({"source": "presentation"})
if pres:
    print(f"Keys: {list(pres.keys())}")
    print(f"Topic: {pres.get('topic')}")
    print(f"Keywords (first 5): {pres.get('keywords', [])[:5]}")
    print(f"Has embedding: {'embedding' in pres}")
    if 'embedding' in pres:
        print(f"Embedding dimension: {len(pres['embedding'])}")

# Sample KB doc
print("\n" + "="*60)
print("KNOWLEDGE BASE SAMPLE")
print("="*60)
kb = coll.find_one({"source": "knowledge_base"})
if kb:
    print(f"Keys: {list(kb.keys())}")
    print(f"Topic: {kb.get('topic')}")
    print(f"Keywords (first 5): {kb.get('keywords', [])[:5]}")
    print(f"Has embedding: {'embedding' in kb}")
    if 'embedding' in kb:
        print(f"Embedding dimension: {len(kb['embedding'])}")
    print(f"\nContent preview (first 200 chars):")
    print(kb.get('content', '')[:200])

# Search for "machine learning"
print("\n" + "="*60)
print("SEARCH TEST: 'machine learning'")
print("="*60)
ml_docs = list(coll.find(
    {"$text": {"$search": "machine learning"}},
    {"topic": 1, "source": 1, "keywords": 1}
).limit(3))

for doc in ml_docs:
    print(f"- {doc.get('topic')} (source: {doc.get('source')})")