// Names used by the dated football lineup snapshot.
const footballKo = Object.fromEntries(`
AEK|AEK 아테네
AZ|AZ 알크마르
Alavés|알라베스
Anderlecht|안데를레흐트
Angers|앙제
Ararat-Armenia|아라라트아르메니아
Arsenal|아스널
Aston Villa|애스턴 빌라
Atalanta|아탈란타
Athletic|아틀레틱 빌바오
Atlético|아틀레티코 마드리드
Augsburg|아우크스부르크
Auxerre|오세르
Barcelona|바르셀로나
Bayern|바이에른 뮌헨
Benfica|벤피카
Beşiktaş|베식타시
Bodø/Glimt|보되/글림트
Bologna|볼로냐
Bournemouth|본머스
Bremen|베르더 브레멘
Brentford|브렌트퍼드
Brest|브레스트
Brighton|브라이턴
Cagliari|칼리아리
Celje|첼레
Celta|셀타 비고
Celtic|셀틱
Chelsea|첼시
Club Brugge|클뤼프 브뤼허
Cologne|쾰른
Como|코모
Coventry|코번트리
Crystal Palace|크리스털 팰리스
Deportivo|데포르티보
Dinamo Zagreb|디나모 자그레브
Dortmund|도르트문트
Elche|엘체
Elversberg|엘버스베르크
Espanyol|에스파뇰
Everton|에버턴
Fenerbahçe|페네르바흐체
Ferencváros|페렌츠바로시
Feyenoord|페예노르트
Fiorentina|피오렌티나
Frankfurt|프랑크푸르트
Freiburg|프라이부르크
Frosinone|프로시노네
Fulham|풀럼
Galatasaray|갈라타사라이
Genoa|제노아
Getafe|헤타페
Gladbach|묀헨글라트바흐
Hamburg|함부르크
Hapoel Beer-Sheva|하포엘 베르셰바
Hoffenheim|호펜하임
Hull|헐 시티
Inter|인터 밀란
Ipswich|입스위치
Jagiellonia|야기엘로니아
Juventus|유벤투스
LASK|LASK 린츠
Lazio|라치오
Le Havre|르아브르
Le Mans|르망
Lecce|레체
Lech Poznań|레흐 포즈난
Leeds|리즈 유나이티드
Leipzig|라이프치히
Lens|랑스
Levante|레반테
Leverkusen|레버쿠젠
Levski Sofia|레프스키 소피아
Lille|릴
Lillestrøm|릴레스트룀
Liverpool|리버풀
Lorient|로리앙
Lyon|리옹
Mainz|마인츠
Man City|맨체스터 시티
Man Utd|맨체스터 유나이티드
Marseille|마르세유
Milan|AC 밀란
Monaco|모나코
Monza|몬차
Málaga|말라가
NEC|NEC 네이메헌
Napoli|나폴리
Newcastle|뉴캐슬
Nice|니스
Nottingham Forest|노팅엄 포리스트
OFI Crete|OFI 크레타
Olympiacos|올림피아코스
Omonia|오모니아
Osasuna|오사수나
PSG|파리 생제르맹
PSV|PSV 에인트호번
Paderborn|파더보른
Paris FC|파리 FC
Parma|파르마
Porto|포르투
RB Leipzig|RB 라이프치히
Racing|라싱
Rayo Vallecano|라요 바예카노
Real Betis|레알 베티스
Real Madrid|레알 마드리드
Real Sociedad|레알 소시에다드
Rennes|렌
Roma|로마
Sabah|사바흐
Salzburg|잘츠부르크
Sassuolo|사수올로
Schalke|샬케
Sevilla|세비야
Shakhtar|샤흐타르
Slavia Praha|슬라비아 프라하
Slovan|슬로반
Sparta Praha|스파르타 프라하
Sporting|스포르팅
Strasbourg|스트라스부르
Sturm Graz|슈투름 그라츠
Stuttgart|슈투트가르트
Sunderland|선덜랜드
Torino|토리노
Torreense|토헤엔스
Tottenham|토트넘
Toulouse|툴루즈
Troyes|트루아
Udinese|우디네세
Union Berlin|우니온 베를린
Union SG|위니옹 생질루아즈
Valencia|발렌시아
Venezia|베네치아
Viking|비킹
Viktoria Plzeň|빅토리아 플젠
Villarreal|비야레알
A. Maitland-Niles|에인슬리 메이틀랜드나일스
A. Rabiot|아드리앵 라비오
Amo-Ameyaw|아모아메요
Antony|안토니
Antwi|안트위
B. Johnson|브레넌 존슨
Baku|리들레 바쿠
Banzuzi|반주지
Beraldo|베랄두
C. De Ketelaere|샤를 더케텔라러
C. Pulisic|크리스천 풀리식
Castello|카스텔로
Cole Palmer|콜 파머
Cucho Hernández|쿠초 에르난데스
D. Zappacosta|다비데 차파코스타
Davies|알폰소 데이비스
Diego Moreira|디에구 모레이라
Digne|뤼카 디뉴
Dro|드로
Díaz|루이스 디아스
E. Martinez|에밀리아노 마르티네스
Ederson|에데르송
El Aynaoui|엘아이나위
El Mourabet*|엘무라베트*
Ez Abde|에즈 압데
F. Jørgensen|필리프 요르겐센
F. Kessié*|프랑크 케시에*
F. Torres|페란 토레스
Fermín|페르민 로페스
G. Jesus|가브리에우 제주스
G. Martín|헤라르드 마르틴
G. Scamacca|잔루카 스카마카
Godts|고츠
Gonçalo Ramos|곤살루 하무스
Gruda|브라얀 그루다
H. Armstrong|해리슨 암스트롱
H. Bellerín|엑토르 베예린
Hakimi|아슈라프 하키미
Isco|이스코
J. Acheampong|조시 아체암퐁
J. Branthwaite|재러드 브랜스웨이트
J. Grealish|잭 그릴리시
J. Henderson|조던 헨더슨
J. Neves|주앙 네베스
J. Pickford|조던 픽퍼드
J. Rowe|조너선 로
J. Tarkowski|제임스 타코우스키
James Garner|제임스 가너
Joan García|조안 가르시아
Joao Pedro|주앙 페드루
Jules Koundé|쥘 쿤데
K. Adeyemi|카림 아데예미
K. Coulibaly|쿨리발리
K. De Winter|코니 더윈터
K. Dewsbury-Hall|키어넌 듀스버리홀
Kane|해리 케인
Kimmich|요주아 키미히
Kvaratskhelia|흐비차 크바라츠헬리아
L. Bernasconi|로렌초 베르나스코니
L. Hernandez|뤼카 에르난데스
L. Samardžić|라자르 사마르지치
Laimer|콘라트 라이머
Lamine Yamal|라민 야말
Levi Colwill|리바이 콜윌
Luka Modrić|루카 모드리치
M. Caicedo|모이세스 카이세도
M. Carnesecchi|마르코 카르네세키
M. Keane|마이클 킨
M. Lacroix|막상스 라크루아
M. Rogers|모건 로저스
Maignan|마이크 메냥
Marc Bartra|마르크 바르트라
Marc Roca|마르크 로카
Mario Gila|마리오 힐라
Mitchell|미첼
Natan|나탕
Neuer|마누엘 노이어
Nkunku|크리스토페르 은쿤쿠
Nusa|안토니오 누사
Olise|마이클 올리세
Orbán|빌리 오르반
Ortega*|오르테가*
Oso|오소
P. D. Diop|디오프
P. Estupiñán|페르비스 에스투피냔
P. Fornals|파블로 포르날스
Pau Cubarsí|파우 쿠바르시
Pavlović|알렉산다르 파블로비치
Pedri|페드리
Pedro Neto|페드루 네투
Pep Chavarria|페프 차바리아
Raum|다비트 라움
Reyna|조바니 레이나
Rodri|로드리
Rômulo|호물루
S. Chukwueze|새뮤얼 추쿠에제
S. Kolašinac|세아드 콜라시나츠
S. Pavlović|스트라히냐 파블로비치
Safonov|마트베이 사포노프
Saibari|이스마엘 사이바리
T. Barry|티에르노 바리
T. Kristensen|토마스 크리스텐센
Tah|요나탄 타
Upamecano|다요 우파메카노
V. Gómez|빅토르 고메스
Vandevoordt|마르턴 판더포르트
Xavi Espart|차비 에스파르트
Yassine|야신
Zabarnyi|일리야 자바르니
Álvaro Vallés|알바로 바예스
Jakub Markovic|야쿠프 마르코비치
Tomas Holes|토마시 홀레시
David Zima|다비드 지마
Ange N'Guessan|앙제 은게상
Ange Caumenan N'Guessan|앙제 카우메난 은게상
Tomas Vlcek|토마시 블체크
Oskar Kubiak|오스카르 쿠비아크
Wiktor Nowak|빅토르 노바크
David Moses|다비드 모지스
Mubarak Suleiman|무바라크 술레이만
Emmanuel Ayaosi|에마누엘 아야오시
Emmanuel Dennis Ayaosi|에마누엘 데니스 아야오시
Lukas Provod|루카시 프로보드
Danijel Sturm|다니옐 슈투름
N'Golo Kante|은골로 캉테
Marco Asensio|마르코 아센시오
Mert Muldur|메르트 뮐뒤르
Jayden Oosterwolde|제이든 오스트르볼더
Archie Brown|아치 브라운
Nathan Ake|네이선 아케
M. Skriniar|밀란 슈크리니아르
Milan Skriniar|밀란 슈크리니아르
Nelson Semedo|넬송 세메두
M. Guendouzi|마테오 겐두지
Oguz Aydin|오우즈 아이든
M. Greenwood|메이슨 그린우드
Kerem Akturkoglu|케렘 아크튀르콜루
Vedat Muriqi|베다트 무리키
Erling Haaland|엘링 홀란
Bukayo Saka|부카요 사카
Declan Rice|데클런 라이스
William Saliba|윌리엄 살리바
Gabriel Magalhaes|가브리에우 마갈량이스
Jude Bellingham|주드 벨링엄
Kylian Mbappe|킬리안 음바페
Vinicius Junior|비니시우스 주니오르
Rodrygo|호드리구
Harry Kane|해리 케인
Manuel Neuer|마누엘 노이어
Jamal Musiala|자말 무시알라
Lautaro Martinez|라우타로 마르티네스
Nicolo Barella|니콜로 바렐라
Alessandro Bastoni|알레산드로 바스토니
Mohamed Salah|모하메드 살라
Bruno Fernandes|브루노 페르난데스
Marcus Rashford|마커스 래시퍼드
Victor Gyokeres|빅토르 요케레스`.trim().split('\n').map(row => row.split('|')));
Object.assign(footballKo, Object.fromEntries(`
Tomáš Holeš|토마시 홀레시
Tomáš Vlček|토마시 블체크
Oğuz Aydın|오우즈 아이든
Kerem Aktürkoğlu|케렘 아크튀르콜루
N'Golo Kanté|은골로 캉테
Matteo Guendouzi|마테오 겐두지
Milan Škriniar|밀란 슈크리니아르
Mert Müldür|메르트 뮐뒤르
Nathan Aké|네이선 아케
Mubarak Suleiman|무바라크 술레이만
E. Ayaosi|에마누엘 아야오시
M. Suleiman|무바라크 술레이만
D. Sturm|다니옐 슈투름
J. Markovic|야쿠프 마르코비치
A. N'Guessan|앙제 은게상
Gianluigi Donnarumma|지안루이지 돈나룸마
Josko Gvardiol|요슈코 그바르디올
Marc Guehi|마크 게히
Ruben Dias|후벵 디아스
Nico O'Reilly|니코 오라일리
Elliot Anderson|엘리엇 앤더슨
Enzo Fernandez|엔조 페르난데스
Jeremy Doku|제레미 도쿠
Felix Nmecha|펠릭스 은메차
Abdukodir Khusanov|아브두코디르 후사노프
Phil Foden|필 포든
Gabriel|가브리엘
Gabriel Veiga|가브리 베이가
Wesley|웨슬리
Martim Fernandes|마르팀 페르난드스
Pablo Rosario|파블로 로사리오
Borja Sainz|보르하 사인스
Marten De Roon|마르턴 더룬
Donyell Malen|도니얼 말런
Rayan Cherki|라얀 셰르키
Iliman Ndiaye|일리만 은디아예
`.trim().split('\n').map(row => row.split('|'))));
