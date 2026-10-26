from pathlib import Path
import json
R=Path(__file__).resolve().parents[1]
a=[]
def add(i,y,title,url,kind='normative',lang='en',pair='',note=''):
 a.append(dict(id=i,year=y,title=title,url=url,kind=kind,lang=lang,pair_id=pair,scope_note=note))
base='https://www.unesco.org/en/legal-affairs/'
for i,y,t,s in [
('HAGUE1954',1954,'Convention for the Protection of Cultural Property in Armed Conflict','convention-protection-cultural-property-event-armed-conflict-regulations-execution-convention'),
('TRAFFIC1970',1970,'Illicit Import Export and Transfer of Ownership of Cultural Property','convention-means-prohibiting-and-preventing-illicit-import-export-and-transfer-ownership-cultural'),
('UNDERWATER2001',2001,'Protection of the Underwater Cultural Heritage','convention-protection-underwater-cultural-heritage'),
('ICH2003',2003,'Safeguarding of the Intangible Cultural Heritage','convention-safeguarding-intangible-cultural-heritage'),
('DIVERSITY2005',2005,'Diversity of Cultural Expressions','convention-protection-and-promotion-diversity-cultural-expressions'),
('REC1956',1956,'International Principles Applicable to Archaeological Excavations','recommendation-international-principles-applicable-archaeological-excavations'),
('REC1962',1962,'Beauty and Character of Landscapes and Sites','recommendation-concerning-safeguarding-beauty-and-character-landscapes-and-sites'),
('REC1968',1968,'Cultural Property Endangered by Public or Private Works','recommendation-concerning-preservation-cultural-property-endangered-public-or-private-works'),
('REC1972',1972,'Protection at National Level of Cultural and Natural Heritage','recommendation-concerning-protection-national-level-cultural-and-natural-heritage'),
('REC1976',1976,'Safeguarding and Contemporary Role of Historic Areas','recommendation-concerning-safeguarding-and-contemporary-role-historic-areas'),
('MOVABLE1978',1978,'Protection of Movable Cultural Property','recommendation-protection-movable-cultural-property'),
('FOLKLORE1989',1989,'Safeguarding of Traditional Culture and Folklore','recommendation-safeguarding-traditional-culture-and-folklore'),
('HUL2011',2011,'Historic Urban Landscape','recommendation-historic-urban-landscape-including-glossary-definitions'),
('MUSEUM2015',2015,'Museums and Collections Diversity and Role in Society','recommendation-concerning-protection-and-promotion-museums-and-collections-their-diversity-and-their'),
('DOCUMENT2015',2015,'Documentary Heritage including Digital Form','recommendation-concerning-preservation-and-access-documentary-heritage-including-digital-form'),
('DIVERSITY2001',2001,'Universal Declaration on Cultural Diversity','unesco-universal-declaration-cultural-diversity'),
('DESTRUCTION2003',2003,'Intentional Destruction of Cultural Heritage','unesco-declaration-concerning-intentional-destruction-cultural-heritage'),
('DIGITAL2003',2003,'Charter on the Preservation of Digital Heritage','charter-preservation-digital-heritage')]:add(i+'_en',y,t,base+s,pair=i)
add('WH1972_en',1972,'World Heritage Convention','https://whc.unesco.org/en/conventiontext/',pair='WH1972')
add('WH1972_zh',1972,'保护世界文化和自然遗产公约','https://www.un.org/zh/documents/treaty/whc',lang='zh',pair='WH1972')
add('HUL2011_zh',2011,'关于城市历史景观的建议书','https://whc.unesco.org/document/135557',lang='zh',pair='HUL2011')
add('MONDIACULT2022_en',2022,'MONDIACULT 2022 Final Declaration','https://www.unesco.org/en/articles/unesco-world-conference-cultural-policies-and-sustainable-development-mondiacult-2022')
add('MONDIACULT2025_en',2025,'MONDIACULT 2025 Outcome Document','https://www.unesco.org/sites/default/files/medias/fichiers/2025/09/EN_MONDIACULT_Outcome_Document%20Final%2027.09.25.pdf')
add('MONDIACULT_REPORT2025_en',2025,'MONDIACULT 2025 Narrative Report','https://www.unesco.org/sites/default/files/medias/fichiers/2026/02/Report%20MONDIACULT%202025%20%26%20Annexes%20Dec.%202025%20FW.pdf','report',note='December 2025 report; hosted February 2026; annexes included')
add('EVALUATION2013_en',2013,'Evaluation of Standard-setting Work: 2003 Convention','https://ich.unesco.org/doc/src/IOS-EVS-PI-129_REV.-EN.pdf','report')
add('COURIER1970_en',2020,'The 1970 Convention: Cultural diversity before the letter of the law','https://courier.unesco.org/en/articles/1970-convention-cultural-diversity-letter-law','news')
add('MIDDLEEAST2026_en',2026,'UNESCO concern over heritage amidst escalating violence in Middle East','https://www.unesco.org/en/articles/unesco-expresses-concern-over-protection-cultural-heritage-sites-amidst-escalating-violence-middle','news')
add('UNSC2347_en',2017,'Security Council adopts Resolution 2347: cultural heritage','https://press.un.org/en/2017/sc12764.doc.htm','news',note='UN meeting coverage; not resolution full text')
(R/'config/sources.json').write_text(json.dumps(a,ensure_ascii=False,indent=2))
