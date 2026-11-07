"""بيانات الهدايا: أسئلة + قاعدة هدايا + خوارزمية الترتيب (ثنائية اللغة).
هذا الملف لا يعتمد على Kivy، فيمكن تجربته وحده.
"""

# ---------------------------------------------------------------
# أسماء الوسوم (تظهر في سبب الاقتراح)
# ---------------------------------------------------------------
TAG_NAMES = {
    'tech': ('Technology', 'التقنية'),
    'beauty': ('Fashion & beauty', 'الموضة والجمال'),
    'sport': ('Sports', 'الرياضة'),
    'read': ('Reading & learning', 'القراءة والتعلّم'),
    'food': ('Food & cooking', 'الطعام والطبخ'),
    'art': ('Art & crafts', 'الفن والأعمال اليدوية'),
    'gaming': ('Gaming', 'الألعاب'),
    'anime': ('Anime & manga', 'الأنمي والمانغا'),
    'travel': ('Travel & outdoors', 'السفر والطبيعة'),
    'home': ('Home & decor', 'المنزل والديكور'),
    'faith': ('Religion', 'الدين'),
    'practical': ('Practical', 'عملية'),
    'sentimental': ('Sentimental', 'عاطفية'),
    'fun': ('Fun', 'ممتعة'),
    'luxury': ('Luxurious', 'فاخرة'),
    'homebody': ('Loves staying in', 'تناسب محبّ المنزل'),
    'social': ('Social', 'تناسب الاجتماعي'),
    'adventurous': ('Adventurous', 'تناسب المغامر'),
    'creative': ('Creative', 'تناسب المبدع'),
    'calm': ('Calm', 'تناسب الهادئ'),
}

# ---------------------------------------------------------------
# قاعدة الهدايا
# (المعرّف، الإنجليزية، العربية، الجنس m/f/None، الأعمار، الميزانية 1-3، الوسوم، العلاقات المسموحة)
# الأعمار: c طفل ≤12 ، t مراهق 13-19 ، y شاب 20-35 ، a بالغ 36-55 ، s كبير 56+
# الميزانية: 1 بسيطة ، 2 متوسطة ، 3 مرتفعة
# العلاقات: partner parent sibling friend colleague relative (None = الكل)
# ---------------------------------------------------------------
ALL = None
NO_COL = {'partner', 'parent', 'sibling', 'friend', 'relative'}

GIFTS = [
    # --- تقنية ---
    ('earbuds', 'Wireless earbuds', 'سماعات أذن لاسلكية', None, 'tya', 2, 'tech practical', ALL),
    ('powerbank', 'Power bank', 'شاحن متنقل (باور بانك)', None, 'tyas', 1, 'tech practical', ALL),
    ('smartwatch', 'Smart watch', 'ساعة ذكية', None, 'tya', 3, 'tech sport luxury', ALL),
    ('fitband', 'Fitness tracker band', 'سوار تتبّع اللياقة', None, 'tya', 2, 'tech sport practical', ALL),
    ('btspeaker', 'Bluetooth speaker', 'مكبّر صوت بلوتوث', None, 'tya', 2, 'tech fun social', ALL),
    ('phonecase', 'Custom phone case with a photo or name', 'غطاء هاتف مخصص بصورة أو اسم', None, 'ty', 1, 'tech personal sentimental fun', ALL),
    ('wirelesscharger', 'Wireless charging stand', 'حامل شحن لاسلكي', None, 'tya', 2, 'tech practical', ALL),
    ('ereader', 'E-book reader', 'قارئ كتب إلكترونية', None, 'ya', 3, 'read tech calm homebody', ALL),
    ('ledlights', 'Smart LED room lights', 'إضاءة LED ذكية للغرفة', None, 'tya', 1, 'tech home fun creative', ALL),
    ('gamingheadset', 'Gaming headset', 'سماعة رأس للألعاب', None, 'ty', 2, 'gaming tech', ALL),
    ('controller', 'Game controller', 'يد تحكّم للألعاب', None, 'tya', 2, 'gaming tech fun', ALL),
    ('gamecard', 'PlayStation / Xbox / Steam gift card', 'بطاقة رصيد PlayStation / Xbox / Steam', None, 'tya', 1, 'gaming fun practical', ALL),
    ('headphones', 'Noise-cancelling headphones', 'سماعات عازلة للضجيج', None, 'tya', 3, 'tech luxury practical', ALL),
    # --- جمال وموضة ---
    ('perfume_f', 'Perfume for her', 'عطر نسائي', 'f', 'tyas', 2, 'beauty fragrance luxury', NO_COL),
    ('perfume_m', 'Cologne for him', 'عطر رجالي', 'm', 'tyas', 2, 'beauty fragrance luxury', NO_COL),
    ('oud', 'Oud and bukhoor set', 'مجموعة عود وبخور', None, 'yas', 2, 'fragrance home faith luxury', ALL),
    ('handbag', 'Handbag', 'حقيبة يد', 'f', 'tya', 3, 'beauty luxury practical', ALL),
    ('scarf', 'Elegant scarf', 'وشاح أنيق', 'f', 'yas', 1, 'beauty practical', ALL),
    ('classicwatch', 'Classic wrist watch', 'ساعة يد كلاسيكية', None, 'tyas', 3, 'beauty luxury practical', ALL),
    ('wallet', 'Leather wallet (can be engraved)', 'محفظة جلدية (يمكن نقش اسمه عليها)', 'm', 'tyas', 2, 'beauty practical luxury personal', ALL),
    ('sunglasses', 'Sunglasses', 'نظارات شمسية', None, 'tya', 2, 'beauty fun social', ALL),
    ('jewelry', 'Necklace or bracelet', 'قلادة أو سوار', 'f', 'tya', 2, 'beauty sentimental luxury', NO_COL),
    ('pen', 'Premium pen set', 'طقم قلم فاخر', None, 'yas', 2, 'luxury practical read', ALL),
    ('skincare', 'Skincare gift set', 'مجموعة عناية بالبشرة', 'f', 'tya', 2, 'beauty practical', ALL),
    ('makeup', 'Makeup palette', 'باليت مكياج', 'f', 'tya', 2, 'beauty fun creative', ALL),
    ('beardkit', 'Beard & grooming kit', 'طقم عناية باللحية', 'm', 'tya', 2, 'beauty practical', ALL),
    ('hoodie', 'Cozy hoodie', 'هودي دافئ', None, 'ty', 2, 'sport fun practical', ALL),
    ('sneakers', 'Trendy sneakers', 'حذاء رياضي عصري', None, 'tya', 3, 'sport beauty practical', ALL),
    # --- رياضة ---
    ('bottle', 'Insulated water bottle', 'قارورة ماء حرارية', None, 'tyas', 1, 'sport practical travel', ALL),
    ('gymbag', 'Gym bag', 'حقيبة رياضة', None, 'tya', 2, 'sport practical', ALL),
    ('football', 'Football', 'كرة قدم', None, 'ct', 1, 'sport fun social', ALL),
    ('bands', 'Resistance bands set', 'مجموعة أحبال مقاومة', None, 'ya', 1, 'sport practical homebody', ALL),
    ('jersey', 'Favorite team jersey', 'قميص فريقه المفضل', None, 'tya', 2, 'sport fun personal', ALL),
    ('scooter', 'Kick scooter', 'سكوتر', None, 'ct', 3, 'sport fun', ALL),
    # --- قراءة وتعلّم ---
    ('book', 'A book in their favorite field', 'كتاب في مجاله المفضل', None, 'tyas', 1, 'read practical calm homebody', ALL),
    ('bookseries', 'Bestselling book series', 'سلسلة كتب شهيرة', None, 'tya', 2, 'read calm homebody', ALL),
    ('notebook', 'Notebook and nice pen', 'دفتر أنيق مع قلم', None, 'tya', 1, 'read creative practical', ALL),
    ('readlamp', 'Reading lamp', 'مصباح قراءة', None, 'yas', 1, 'read home calm homebody', ALL),
    ('course', 'Online course (language or skill)', 'دورة تعليمية أونلاين (لغة أو مهارة)', None, 'tya', 2, 'read tech practical', ALL),
    ('langapp', 'Language-learning subscription', 'اشتراك لتعلّم لغة', None, 'tya', 1, 'read tech practical', ALL),
    ('kidbooks', 'Illustrated story books', 'كتب قصص مصوّرة', None, 'c', 1, 'read fun calm', ALL),
    # --- طعام وطبخ ---
    ('chocolate', 'Premium chocolate box', 'علبة شوكولاتة فاخرة', None, 'ctyas', 1, 'food sweets sentimental', ALL),
    ('dates', 'Dates and nuts gift basket', 'سلة تمور ومكسّرات', None, 'tyas', 1, 'food sweets faith practical', ALL),
    ('coffeeset', 'Coffee set', 'طقم قهوة', None, 'yas', 2, 'food home calm luxury', ALL),
    ('teaset', 'Fine tea gift set', 'مجموعة شاي فاخر', None, 'yas', 1, 'food calm home', ALL),
    ('airfryer', 'Air fryer or blender', 'قلاية هوائية أو خلاط', None, 'yas', 2, 'food practical home', ALL),
    ('bakingset', 'Baking tools set', 'طقم أدوات الحلويات', None, 'tya', 1, 'food creative home', ALL),
    ('honey', 'Honey basket', 'سلة عسل', None, 'as', 1, 'food home practical', ALL),
    ('customcake', 'Custom birthday cake', 'كعكة عيد ميلاد مخصصة', None, 'ctyas', 1, 'food sweets fun social', ALL),
    # --- فن وإبداع ---
    ('sketch', 'Sketching and drawing set', 'طقم رسم وتخطيط', None, 'cty', 1, 'art creative calm', ALL),
    ('paintnum', 'Paint-by-numbers canvas', 'لوحة تلوين بالأرقام', None, 'tya', 1, 'art creative calm homebody', ALL),
    ('instantcam', 'Instant camera', 'كاميرا فورية', None, 'tya', 2, 'art tech fun creative social sentimental', ALL),
    ('portrait', 'Hand-drawn portrait', 'بورتريه مرسوم يدويًا', None, 'tya', 2, 'art sentimental personal', ALL),
    ('diykit', 'DIY craft kit', 'مجموعة أعمال يدوية', None, 'cty', 1, 'creative art fun', ALL),
    # --- ألعاب جماعية وتركيب ---
    ('boardgame', 'Board game for friends and family', 'لعبة جماعية (بورد غيم)', None, 'ctya', 1, 'fun social gaming', ALL),
    ('puzzle', 'Jigsaw puzzle', 'أحجية تركيب (بازل)', None, 'ctyas', 1, 'calm homebody fun', ALL),
    ('lego', 'Building blocks set', 'مجموعة مكعبات تركيب', None, 'ctya', 2, 'creative fun gaming', ALL),
    # --- سفر وطبيعة ---
    ('suitcase', 'Travel suitcase', 'حقيبة سفر', None, 'yas', 3, 'travel practical luxury', ALL),
    ('travelkit', 'Travel comfort kit', 'طقم راحة للسفر', None, 'ya', 1, 'travel practical', ALL),
    ('lantern', 'Camping lantern', 'فانوس تخييم', None, 'tya', 1, 'adventurous travel practical', ALL),
    ('daytrip', 'A day trip or outdoor experience', 'رحلة ليوم واحد أو تجربة في الطبيعة', None, 'tya', 2, 'travel adventurous social fun', ALL),
    ('backpack', 'Hiking backpack', 'حقيبة ظهر للمشي والتنزّه', None, 'tya', 2, 'travel adventurous sport practical', ALL),
    ('picnic', 'Picnic set', 'طقم نزهة', None, 'yas', 2, 'travel home social food', ALL),
    # --- منزل ---
    ('candles', 'Scented candles', 'شموع معطّرة', None, 'yas', 1, 'home calm fragrance sentimental', ALL),
    ('plant', 'Decorative indoor plant', 'نبتة زينة للمنزل', None, 'tyas', 1, 'home calm', ALL),
    ('wallart', 'Wall art or framed print', 'لوحة جدارية', None, 'yas', 2, 'home art', ALL),
    ('blanket', 'Cozy blanket', 'بطانية دافئة', None, 'tyas', 2, 'home calm homebody practical', ALL),
    ('bedding', 'Luxury bedding set', 'طقم أغطية سرير فاخر', None, 'yas', 3, 'home luxury practical', ALL),
    ('mug', 'Personalized mug', 'كوب مطبوع باسمه', None, 'tyas', 1, 'home personal fun sentimental practical', ALL),
    ('tablelamp', 'Stylish table lamp', 'مصباح طاولة أنيق', None, 'tya', 2, 'home art', ALL),
    ('moonlamp', 'Moon night lamp', 'مصباح القمر الليلي', None, 'cty', 1, 'home fun sentimental', ALL),
    # --- إيمان وروحانيات ---
    ('quran', 'Quran with an elegant cover', 'مصحف بغلاف أنيق', None, 'tyas', 2, 'faith sentimental', ALL),
    ('prayermat', 'Prayer mat', 'سجادة صلاة', None, 'tyas', 1, 'faith practical', ALL),
    ('misbaha', 'Prayer beads (misbaha)', 'مسبحة', None, 'tyas', 1, 'faith sentimental', ALL),
    ('islamicbook', 'Islamic book', 'كتاب إسلامي', None, 'tyas', 1, 'faith read calm', ALL),
    # --- أطفال ---
    ('plush', 'Small teddy bear or plush toy', 'دبدوب صغير أو دمية قطنية', None, 'ctyas', 1, 'fun sentimental', ALL),
    ('rccar', 'Remote-control car', 'سيارة تحكّم عن بعد', 'm', 'ct', 2, 'fun gaming', ALL),
    ('doll', 'Doll with accessories', 'دمية مع إكسسواراتها', 'f', 'c', 1, 'fun creative', ALL),
    ('colorset', 'Coloring and drawing set', 'أدوات تلوين ورسم', None, 'c', 1, 'art creative fun', ALL),
    ('schoolbag', 'School backpack', 'حقيبة مدرسية', None, 'ct', 2, 'practical', ALL),
    # --- رومانسية (للشريك) ---
    ('dinner', 'Romantic dinner for two', 'عشاء رومانسي لشخصين', None, 'yas', 2, 'sentimental luxury social', {'partner'}),
    ('flowers', 'Flower bouquet', 'باقة ورد', 'f', 'tyas', 1, 'sentimental beauty', NO_COL),
    ('couplebracelets', 'Matching bracelets', 'أساور متطابقة', None, 'tya', 1, 'sentimental personal fun', {'partner'}),
    ('getaway', 'Weekend getaway', 'عطلة نهاية أسبوع', None, 'ya', 3, 'travel sentimental luxury adventurous', {'partner'}),
    # --- عمل وزملاء ---
    ('deskorg', 'Desk organizer', 'منظّم مكتب', None, 'ya', 1, 'practical home', {'colleague', 'friend'}),
    ('plantdesk', 'Small desk plant', 'نبتة صغيرة للمكتب', None, 'yas', 1, 'home calm practical', {'colleague', 'friend'}),
    # --- للوالدين وكبار السن ---
    ('massage', 'Massage cushion', 'وسادة تدليك', None, 'as', 2, 'practical calm homebody', {'parent', 'relative', 'partner'}),
    ('robe', 'Warm robe and slippers', 'روب منزلي ونعال دافئة', None, 'as', 1, 'home practical calm homebody', ALL),
    ('bpmonitor', 'Blood pressure monitor', 'جهاز قياس الضغط', None, 's', 2, 'practical', {'parent', 'relative'}),
    ('familyframe', 'Family photo frame', 'إطار صورة عائلية', None, 'as', 1, 'sentimental personal home', {'parent', 'relative', 'sibling'}),
    ('traditionaltea', 'Traditional tea set', 'طقم شاي تقليدي', None, 'as', 2, 'food home faith sentimental', ALL),
    ('qurandstand', 'Wooden Quran stand', 'حامل مصحف خشبي', None, 'yas', 1, 'faith home practical', ALL),
    # --- اشتراكات ---
    ('netmonth', 'Monthly internet subscription', 'اشتراك إنترنت شهري', None, 'tyas', 1, 'tech practical', ALL),
    ('netyear', 'Annual internet subscription', 'اشتراك إنترنت سنوي', None, 'tyas', 2, 'tech practical', ALL),
    ('streammonth', 'Monthly streaming subscription (Netflix / Shahid)', 'اشتراك شهري في منصة مشاهدة (Netflix / Shahid)', None, 'tya', 1, 'tech fun homebody', ALL),
    ('streamyear', 'Annual streaming subscription (Netflix / Shahid)', 'اشتراك سنوي في منصة مشاهدة (Netflix / Shahid)', None, 'tya', 2, 'tech fun homebody', ALL),
    # --- متوسطة جديدة ---
    ('kbmouse', 'Gaming keyboard and mouse', 'لوحة مفاتيح وماوس للألعاب', None, 'ty', 2, 'gaming tech practical', ALL),
    ('campset', 'Tent and camping gear', 'خيمة ومعدات تخييم', None, 'tya', 2, 'adventurous travel practical', ALL),
    ('smartspeaker', 'Smart speaker', 'مكبّر صوت ذكي', None, 'tya', 2, 'tech home practical', ALL),
    # --- غالية ---
    # --- شائعة: للجميع ---
    ('teddybig', 'Big teddy bear', 'دبدوب كبير', None, 'ctyas', 2, 'sentimental fun home', NO_COL),
    ('stickers', 'Anime sticker pack', 'ستيكرات أنمي', None, 'tya', 1, 'anime fun creative', ALL),
    ('animefigure', 'Anime figure', 'تمثال أنمي (Figure)', None, 'tya', 2, 'anime fun art', ALL),
    ('animeposter', 'Anime wall poster', 'ملصق جداري أنمي', None, 'tya', 1, 'anime home art', ALL),
    ('manga', 'Manga or comic books', 'مانغا أو قصص مصوّرة', None, 'ctya', 1, 'anime read fun calm homebody', ALL),
    ('animehoodie', 'Anime hoodie or T-shirt', 'هودي أو تيشيرت أنمي', None, 'tya', 2, 'anime fun', ALL),
    ('keychain', 'Keychain with their name', 'حلقة مفاتيح مخصصة باسمه', None, 'tyas', 1, 'personal sentimental fun', ALL),
    ('photoshirt', 'T-shirt with their photo', 'تيشيرت بصورته', None, 'tya', 1, 'personal fun sentimental', ALL),
    ('ledframe', 'LED photo frame', 'إطار صورة LED', None, 'tyas', 1, 'personal sentimental home creative', ALL),
    ('balloons', 'Birthday balloon decoration set', 'زينة بالونات لعيد الميلاد', None, 'ctya', 1, 'fun social', ALL),
    ('socks', 'Cozy cute socks', 'جوارب دافئة لطيفة', None, 'ctyas', 1, 'home calm homebody fun', ALL),
    ('memories', 'Handwritten letter or a video of memories', 'رسالة بخط اليد أو فيديو ذكريات', None, 'tyas', 1, 'sentimental personal', {'partner', 'parent', 'sibling', 'friend', 'relative'}),
    ('starmap', 'Star map of their birth night', 'خريطة النجوم ليلة ميلاده', None, 'ya', 2, 'sentimental personal art home', {'partner', 'friend', 'sibling'}),
    ('digiframe', 'Digital photo frame', 'إطار صور رقمي', None, 'yas', 2, 'tech sentimental home personal', ALL),
    # --- شائعة: للبنات ---
    ('roseglass', 'Preserved rose in glass (lasts a year)', 'وردة محفوظة في زجاج (تدوم سنة)', 'f', 'tyas', 2, 'beauty sentimental luxury', NO_COL),
    ('flowerchoc', 'Bouquet with chocolates', 'باقة ورد مع شوكولاتة', 'f', 'tyas', 2, 'sentimental sweets beauty', NO_COL),
    ('hairacc', 'Hair accessories set', 'مجموعة إكسسوارات شعر', 'f', 'ctya', 1, 'beauty fun', ALL),
    ('nailkit', 'Nail polish set', 'طقم طلاء أظافر', 'f', 'tya', 1, 'beauty fun creative', ALL),
    ('jewelbox', 'Jewelry box', 'علبة مجوهرات', 'f', 'tyas', 2, 'beauty home luxury', ALL),
    ('namenecklace', 'Name necklace', 'قلادة باسمها', 'f', 'tya', 2, 'beauty personal sentimental', NO_COL),
    ('makeuporg', 'Makeup organizer', 'منظّم مكياج', 'f', 'tya', 2, 'beauty practical home', ALL),
    ('ledmirror', 'LED makeup mirror', 'مرآة LED للمكياج', 'f', 'tya', 2, 'beauty tech practical', ALL),
    ('bodymist', 'Body mist spray', 'بخاخ عطر للجسم', 'f', 'tya', 1, 'fragrance beauty', ALL),
    ('hairtool', 'Hair dryer or straightener', 'مجففة أو مكواة شعر', 'f', 'tya', 2, 'beauty practical tech', ALL),
    ('abaya', 'Abaya or kaftan', 'عباءة أو قفطان', 'f', 'yas', 2, 'beauty faith luxury', NO_COL),
    ('pajamas', 'Elegant pajama set', 'بيجاما أنيقة', 'f', 'tyas', 2, 'home beauty homebody calm', ALL),
    ('tote', 'Printed tote bag', 'حقيبة قماش مطبوعة', 'f', 'tya', 1, 'beauty practical fun', ALL),
    ('koreancare', 'Korean skincare set', 'منتجات عناية كورية', 'f', 'tya', 2, 'beauty practical', ALL),
    # --- شائعة: للأولاد ---
    ('cards', 'Trading cards (Pokemon or football)', 'بطاقات تجميع (بوكيمون أو كرة قدم)', None, 'cty', 1, 'fun gaming sport anime', ALL),
    ('rubik', "Rubik's cube", 'مكعب روبيك', None, 'ctya', 1, 'fun calm creative gaming', ALL),
    ('footballboots', 'Football boots', 'حذاء كرة قدم', 'm', 'tya', 2, 'sport', ALL),
    ('gamingchair', 'Gaming chair', 'كرسي ألعاب (Gaming chair)', None, 'tya', 3, 'gaming tech practical', ALL),
    ('skateboard', 'Skateboard', 'سكيت بورد', None, 'ty', 2, 'sport fun adventurous', ALL),
    ('fishing', 'Fishing set', 'طقم صيد', 'm', 'ya', 2, 'adventurous travel calm', ALL),
    ('laptopbag', 'Laptop backpack', 'حقيبة ظهر للابتوب', None, 'tya', 2, 'tech practical', ALL),
    ('belt', 'Leather belt', 'حزام جلدي', 'm', 'tyas', 1, 'beauty practical luxury', ALL),
    ('carkit', 'Car accessories (phone holder, car perfume)', 'أدوات قيادة (حامل هاتف، عطر سيارة)', None, 'ya', 1, 'practical tech', ALL),
    ('glovesshaker', 'Gym gloves and shaker bottle', 'قفازات رياضة مع شيكر', 'm', 'tya', 1, 'sport practical', ALL),
    ('toolset', 'Tool set', 'طقم أدوات', 'm', 'as', 2, 'practical home', ALL),
    ('mousepad', 'XL gaming mouse pad', 'بساط ماوس كبير للألعاب', None, 'tya', 1, 'gaming tech practical', ALL),
    # --- شائعة: للأطفال ---
    ('slime', 'Slime kit', 'طقم سلايم', None, 'c', 1, 'fun creative', ALL),
    ('drawboard', 'Drawing board', 'سبورة رسم', None, 'c', 1, 'art creative fun', ALL),
    ('kidbike', "Kid's bicycle", 'دراجة أطفال', None, 'c', 3, 'sport fun', ALL),
    ('laptop', 'Laptop (study, work or gaming)', 'لابتوب (للدراسة أو العمل أو الألعاب)', None, 'tya', 3, 'tech practical read creative gaming', ALL),
    ('tablet', 'Tablet', 'جهاز لوحي (تابلت)', None, 'tya', 3, 'tech read creative fun', ALL),
    ('smartphone', 'Smartphone', 'هاتف ذكي', None, 'tyas', 3, 'tech practical social', ALL),
    ('console', 'Game console (PlayStation / Xbox)', 'جهاز ألعاب (PlayStation / Xbox)', None, 'ty', 3, 'gaming tech fun social', ALL),
    ('camera', 'Digital camera or action camera', 'كاميرا رقمية أو كاميرا حركة', None, 'tya', 3, 'tech art travel creative', ALL),
    ('drone', 'Camera drone', 'طائرة مسيّرة بكاميرا (Drone)', None, 'y', 3, 'tech adventurous creative travel', ALL),
    ('escooter', 'Electric scooter or e-bike', 'سكوتر أو دراجة كهربائية', None, 'ty', 3, 'tech sport fun adventurous', ALL),
    ('homegym', 'Home exercise bike or treadmill', 'دراجة ثابتة أو مشّاية للمنزل', None, 'ya', 3, 'sport practical homebody', ALL),
    ('goldjewelry', 'Gold jewelry', 'مجوهرات ذهبية', 'f', 'yas', 3, 'beauty luxury sentimental', NO_COL),
    ('umrah', 'Umrah trip', 'رحلة عمرة', None, 'as', 3, 'faith sentimental travel', {'parent', 'relative', 'partner'}),
    ('bigappliance', 'Big home appliance (washing machine, fridge, TV)', 'جهاز منزلي كبير (غسالة، ثلاجة، تلفاز)', None, 'as', 3, 'practical home', {'parent'}),
    ('espresso', 'Espresso coffee machine', 'آلة قهوة إسبريسو', None, 'ya', 3, 'food home calm luxury', ALL),
    ('leatherjacket', 'Premium leather jacket', 'جاكيت جلدي فاخر', None, 'ya', 3, 'beauty luxury practical', ALL),
    ('projector', 'Home projector', 'جهاز عرض منزلي (Projector)', None, 'ya', 3, 'tech home fun homebody', ALL),
]

# ---------------------------------------------------------------
# الأسئلة: مرتّبة حسب الأهمية. الأسئلة العشرة الأولى هي الأساسية.
# كل سؤال: (المفتاح، نص إنجليزي، نص عربي، [(قيمة، إنجليزي، عربي), ...])
# ---------------------------------------------------------------
YES = ('yes', 'Yes', 'نعم')
NO = ('no', 'No', 'لا')

INTERESTS = [
    ('tech', 'Technology & gadgets', 'التقنية والأجهزة'),
    ('beauty', 'Fashion & beauty', 'الموضة والجمال'),
    ('sport', 'Sports & fitness', 'الرياضة واللياقة'),
    ('read', 'Reading & learning', 'القراءة والتعلّم'),
    ('food', 'Food & cooking', 'الطعام والطبخ'),
    ('art', 'Art & crafts', 'الفن والأعمال اليدوية'),
    ('gaming', 'Gaming', 'الألعاب الإلكترونية'),
    ('anime', 'Anime & manga', 'الأنمي والمانغا'),
    ('travel', 'Travel & outdoors', 'السفر والطبيعة'),
    ('home', 'Home & decor', 'المنزل والديكور'),
    ('faith', 'Religion', 'الدين'),
]

QUESTIONS = [
    ('relation', 'Who is the gift for?', 'لمن هذه الهدية؟', [
        ('partner', 'Husband / wife / partner', 'الزوج / الزوجة / الشريك'),
        ('parent', 'A parent', 'أحد الوالدين'),
        ('sibling', 'Brother / sister', 'أخ / أخت'),
        ('friend', 'A friend', 'صديق / صديقة'),
        ('colleague', 'A colleague', 'زميل / زميلة'),
        ('relative', 'Another relative', 'قريب / قريبة'),
    ]),
    ('gender', 'Is the person male or female?', 'هل الشخص ذكر أم أنثى؟', [
        ('m', 'Male', 'ذكر'),
        ('f', 'Female', 'أنثى'),
    ]),
    ('age', 'How old are they?', 'كم عمر الشخص؟', [
        ('c', '12 or younger', '12 سنة أو أقل'),
        ('t', '13 – 19', 'من 13 إلى 19'),
        ('y', '20 – 35', 'من 20 إلى 35'),
        ('a', '36 – 55', 'من 36 إلى 55'),
        ('s', '56 or older', '56 سنة فأكثر'),
    ]),
    ('budget', 'What is your budget?', 'ما ميزانيتك؟', [
        ('low', 'Low – a small gift', 'منخفضة – هدية بسيطة'),
        ('mid', 'Medium', 'متوسطة'),
        ('high', 'High', 'مرتفعة'),
        ('nolimit', 'No limit – any price, only their taste matters', 'بلا حدود – أي سعر، المهم تفضيلاته'),
    ]),
    ('interest1', 'What is their biggest interest?', 'ما أكبر اهتمام لديه؟', INTERESTS),
    ('interest2', 'Do they have a second interest?', 'هل لديه اهتمام ثانٍ؟',
     INTERESTS + [('none', 'None / not sure', 'لا شيء / لست متأكدًا')]),
    ('style', 'What kind of gift do you want to give?', 'أي نوع من الهدايا تريد تقديمه؟', [
        ('practical', 'Practical & useful', 'عملية ومفيدة'),
        ('sentimental', 'Personal & emotional', 'شخصية وعاطفية'),
        ('fun', 'Fun & surprising', 'ممتعة ومفاجئة'),
        ('luxury', 'Luxurious & elegant', 'فاخرة وأنيقة'),
    ]),
    ('personality', 'How would you describe their personality?', 'كيف تصف شخصيته؟', [
        ('homebody', 'Homebody – loves staying in', 'يحب البقاء في المنزل'),
        ('social', 'Social & outgoing', 'اجتماعي ومحبّ للخروج'),
        ('adventurous', 'Adventurous', 'مغامر'),
        ('creative', 'Creative', 'مبدع'),
        ('calm', 'Calm & thoughtful', 'هادئ ومتأمّل'),
    ]),
    ('closeness', 'How close are you to them?', 'ما مدى قربك منه؟', [
        ('very', 'Very close', 'قريب جدًا'),
        ('close', 'Close', 'قريب'),
        ('casual', 'Not that close', 'علاقة عادية'),
    ]),
    ('personal', 'Would they like a personalized gift (name, photo, engraving)?',
     'هل تعجبه هدية مخصصة (اسم أو صورة أو نقش)؟', [YES, NO]),
    ('handover', 'Will you give it to them in person?', 'هل ستسلّمها له بيدك؟', [
        ('in', 'Yes, in person', 'نعم، شخصيًا'),
        ('ship', 'No, it will be sent', 'لا، ستُرسل إليه'),
    ]),
    ('sweets', 'Do they love sweets and treats?', 'هل يحب الحلويات؟', [YES, NO]),
    ('fragrance', 'Do they enjoy perfumes and scents?', 'هل يحب العطور والروائح؟', [YES, NO]),
    ('phone', 'How much do they use their phone and gadgets?', 'كم يستعمل هاتفه وأجهزته؟', [
        ('heavy', 'A lot', 'كثيرًا'),
        ('low', 'Not much', 'قليلًا'),
    ]),
    ('outdoor', 'Do they prefer being outdoors or at home?', 'هل يفضّل الخروج أم البقاء في المنزل؟', [
        ('out', 'Outdoors', 'الخروج والطبيعة'),
        ('in', 'At home', 'المنزل'),
    ]),
    ('look', 'What is their style?', 'ما أسلوبه في الذوق؟', [
        ('classic', 'Classic', 'كلاسيكي'),
        ('modern', 'Modern', 'عصري'),
        ('sporty', 'Sporty', 'رياضي'),
    ]),
    ('useful', 'What matters more to them in a gift?', 'ما الأهم لديه في الهدية؟', [
        ('looks', 'How it looks', 'شكلها وجمالها'),
        ('useful', 'How useful it is', 'فائدتها'),
    ]),
    ('gadgets', 'Do they already own lots of gadgets?', 'هل يملك أجهزة كثيرة بالفعل؟', [
        ('yes', 'Yes, a lot', 'نعم، الكثير'),
        ('no', 'Not really', 'ليس كثيرًا'),
    ]),
    ('size', 'What size of gift do you prefer?', 'ما حجم الهدية الذي تفضّله؟', [
        ('small', 'Small & easy to wrap', 'صغيرة وسهلة التغليف'),
        ('any', 'Any size', 'أي حجم'),
        ('big', 'A big wow gift', 'كبيرة ولافتة'),
    ]),
    ('experience', 'An experience or a physical item?', 'تجربة نعيشها أم شيء ملموس؟', [
        ('exp', 'An experience', 'تجربة نعيشها'),
        ('obj', 'A physical item', 'شيء ملموس'),
    ]),
]

QUESTION_COUNTS = (10, 15, 20)

# ---------------------------------------------------------------
# تحويل القائمة إلى قواميس
# ---------------------------------------------------------------
_BUDGET = {'low': 1, 'mid': 2, 'high': 3, 'nolimit': None}   # None = بلا حدود: لا قيود ولا أفضلية للسعر


def _gift(row):
    gid, en, ar, gender, ages, budget, tags, rel = row
    return {'id': gid, 'en': en, 'ar': ar, 'gender': gender, 'ages': ages,
            'budget': budget, 'tags': set(tags.split()), 'rel': rel}


GIFT_LIST = [_gift(r) for r in GIFTS]


def score_gift(g, p, strict=3):
    """يرجع (النقاط، قائمة أسباب). strict: 3 كل القيود، 2 بدون العلاقة، 1 بدون الجنس أيضًا."""
    s = 0.0
    why = []
    tags = g['tags']

    # --- قيود صارمة ---
    age = p.get('age')
    if age and age not in g['ages']:
        return -1000.0, why
    if strict >= 3:
        rel = p.get('relation')
        if rel and g['rel'] is not None and rel not in g['rel']:
            return -1000.0, why
    if strict >= 2:
        gen = p.get('gender')
        if gen and g['gender'] and g['gender'] != gen:
            return -1000.0, why
    u = _BUDGET.get(p.get('budget'), 2)
    if u is not None and g['budget'] > u:
        return -1000.0, why

    # --- الميزانية: نطاق مستهدف (متوسطة تفضّل المتوسط، مرتفعة تفضّل الغالي) ---
    if u is not None:
        if g['budget'] == u:
            s += 1.5
            why.append('budget')
        else:
            s -= 2.5 * (u - g['budget'])

    # --- الجنس ---
    if g['gender'] and g['gender'] == p.get('gender'):
        s += 1.5

    # --- الاهتمامات ---
    i1, i2 = p.get('interest1'), p.get('interest2')
    if i1 in tags:
        s += 4.0
        why.append(i1)
    if i2 and i2 != 'none' and i2 in tags:
        s += 2.0
        why.append(i2)

    # --- نوع الهدية ---
    st = p.get('style')
    if st in tags:
        s += 3.0
        why.append(st)
    if p.get('useful') == 'useful' and 'practical' in tags:
        s += 1.5
    if p.get('useful') == 'looks' and ('beauty' in tags or 'luxury' in tags or 'art' in tags):
        s += 1.0

    # --- الشخصية ---
    pe = p.get('personality')
    if pe in tags:
        s += 1.5
        why.append(pe)

    # --- العلاقة والقرب ---
    rel = p.get('relation')
    if rel == 'partner' and g['rel'] == {'partner'}:
        s += 3.0
    if rel == 'colleague' and g['rel'] and 'colleague' in g['rel'] and 'friend' in g['rel']:
        s += 2.0
    cl = p.get('closeness')
    if cl == 'casual':
        if g['budget'] == 3:
            s -= 2.0
        if 'sentimental' in tags:
            s -= 1.0
    elif cl == 'very' and 'sentimental' in tags:
        s += 1.0

    # --- أسئلة نعم/لا ---
    if 'personal' in tags:
        if p.get('personal') == 'yes':
            s += 2.0
            why.append('personal')
        elif p.get('personal') == 'no':
            s -= 1.0
    if 'sweets' in tags:
        s += 2.0 if p.get('sweets') == 'yes' else (-2.0 if p.get('sweets') == 'no' else 0)
    if 'fragrance' in tags:
        s += 2.0 if p.get('fragrance') == 'yes' else (-2.0 if p.get('fragrance') == 'no' else 0)
    if 'tech' in tags:
        if p.get('phone') == 'heavy':
            s += 1.0
        elif p.get('phone') == 'low':
            s -= 1.0
        if p.get('gadgets') == 'yes':
            s -= 2.0
        elif p.get('gadgets') == 'no':
            s += 1.0
    if p.get('outdoor') == 'out' and ({'adventurous', 'travel'} & tags):
        s += 1.5
    if p.get('outdoor') == 'in' and ({'homebody', 'home'} & tags):
        s += 1.0
    lk = p.get('look')
    if lk == 'classic' and 'luxury' in tags:
        s += 1.0
    if lk == 'modern' and 'tech' in tags:
        s += 1.0
    if lk == 'sporty' and 'sport' in tags:
        s += 1.0
    if p.get('size') == 'small' and g['budget'] == 1:
        s += 1.0
    if p.get('size') == 'big' and g['budget'] == 3:
        s += 1.0
    if 'experience' in tags or g['id'] in EXPERIENCE_IDS:
        if p.get('experience') == 'exp':
            s += 3.0
        elif p.get('experience') == 'obj':
            s -= 1.0
        if p.get('handover') == 'ship':
            s -= 3.0
    return s, why


EXPERIENCE_IDS = {'daytrip', 'dinner', 'getaway', 'umrah'}


def recommend(profile, limit=10):
    """يرجع قائمة هدايا مرتبة: [{'gift': g, 'score': s, 'why': [...]}, ...]"""
    for strict in (3, 2, 1):
        out = []
        for g in GIFT_LIST:
            s, why = score_gift(g, profile, strict)
            if s > -500:
                out.append({'gift': g, 'score': s, 'why': why})
        if len(out) >= 6:
            break
    out.sort(key=lambda r: (-r['score'], r['gift']['en']))
    return out[:limit]


def pick_questions(count):
    return QUESTIONS[:count]
