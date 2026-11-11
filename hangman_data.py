"""كلمات لعبة «المشنقة». كل كلمة: (إنجليزي، عربي) وكلاهما كلمة واحدة بلا مسافات.
الفئات: (المعرّف، الاسم بالإنجليزية، الاسم بالعربية)."""

CATS = [
    ('animals', 'Animals', 'حيوانات'),
    ('fruits', 'Fruits & Vegetables', 'فواكه وخضر'),
    ('countries', 'Countries', 'دول'),
    ('food', 'Food & Drinks', 'أكلات ومشروبات'),
    ('jobs', 'Jobs', 'مهن'),
    ('sports', 'Sports', 'رياضة'),
    ('things', 'Things', 'أشياء'),
]

WORDS = {
    'animals': [
        ('Lion', 'أسد'), ('Elephant', 'فيل'), ('Monkey', 'قرد'), ('Camel', 'جمل'),
        ('Giraffe', 'زرافة'), ('Rabbit', 'أرنب'), ('Horse', 'حصان'), ('Dolphin', 'دلفين'),
        ('Eagle', 'نسر'), ('Tiger', 'نمر'), ('Wolf', 'ذئب'), ('Fox', 'ثعلب'),
        ('Turtle', 'سلحفاة'), ('Parrot', 'ببغاء'), ('Spider', 'عنكبوت'), ('Shark', 'قرش'),
        ('Ostrich', 'نعامة'), ('Penguin', 'بطريق'),
    ],
    'fruits': [
        ('Apple', 'تفاح'), ('Banana', 'موز'), ('Orange', 'برتقال'), ('Grapes', 'عنب'),
        ('Lemon', 'ليمون'), ('Cherry', 'كرز'), ('Mango', 'مانجو'), ('Peach', 'خوخ'),
        ('Potato', 'بطاطا'), ('Tomato', 'طماطم'), ('Carrot', 'جزر'), ('Onion', 'بصل'),
        ('Garlic', 'ثوم'), ('Pepper', 'فلفل'), ('Watermelon', 'بطيخ'),
        ('Strawberry', 'فراولة'), ('Dates', 'تمر'),
    ],
    'countries': [
        ('Algeria', 'الجزائر'), ('Morocco', 'المغرب'), ('Tunisia', 'تونس'), ('Egypt', 'مصر'),
        ('France', 'فرنسا'), ('Spain', 'إسبانيا'), ('Italy', 'إيطاليا'), ('Brazil', 'البرازيل'),
        ('Canada', 'كندا'), ('Japan', 'اليابان'), ('Russia', 'روسيا'), ('Turkey', 'تركيا'),
        ('Germany', 'ألمانيا'), ('China', 'الصين'), ('Palestine', 'فلسطين'), ('Qatar', 'قطر'),
        ('Jordan', 'الأردن'), ('Libya', 'ليبيا'), ('Argentina', 'الأرجنتين'),
    ],
    'food': [
        ('Couscous', 'كسكس'), ('Bread', 'خبز'), ('Cheese', 'جبن'), ('Pizza', 'بيتزا'),
        ('Burger', 'برغر'), ('Salad', 'سلطة'), ('Soup', 'شوربة'), ('Rice', 'أرز'),
        ('Honey', 'عسل'), ('Coffee', 'قهوة'), ('Chicken', 'دجاج'), ('Chocolate', 'شوكولاتة'),
        ('Sandwich', 'ساندويتش'), ('Biscuit', 'بسكويت'), ('Sugar', 'سكر'), ('Milk', 'حليب'),
    ],
    'jobs': [
        ('Doctor', 'طبيب'), ('Teacher', 'معلم'), ('Engineer', 'مهندس'), ('Pilot', 'طيار'),
        ('Driver', 'سائق'), ('Farmer', 'فلاح'), ('Baker', 'خباز'), ('Nurse', 'ممرض'),
        ('Judge', 'قاضي'), ('Lawyer', 'محامي'), ('Painter', 'رسام'), ('Soldier', 'جندي'),
        ('Tailor', 'خياط'), ('Singer', 'مغني'), ('Butcher', 'جزار'), ('Chef', 'طباخ'),
        ('Scientist', 'عالم'),
    ],
    'sports': [
        ('Tennis', 'تنس'), ('Boxing', 'ملاكمة'), ('Swimming', 'سباحة'), ('Judo', 'جودو'),
        ('Karate', 'كاراتيه'), ('Golf', 'غولف'), ('Hockey', 'هوكي'), ('Rugby', 'رغبي'),
        ('Cricket', 'كريكيت'), ('Wrestling', 'مصارعة'), ('Archery', 'رماية'),
        ('Fencing', 'مبارزة'), ('Gymnastics', 'جمباز'), ('Marathon', 'ماراثون'),
        ('Referee', 'حكم'), ('Stadium', 'ملعب'), ('Trophy', 'كأس'),
    ],
    'things': [
        ('Table', 'طاولة'), ('Chair', 'كرسي'), ('Window', 'نافذة'), ('Mirror', 'مرآة'),
        ('Clock', 'ساعة'), ('Umbrella', 'مظلة'), ('Key', 'مفتاح'), ('Book', 'كتاب'),
        ('Pen', 'قلم'), ('Lamp', 'مصباح'), ('Phone', 'هاتف'), ('Camera', 'كاميرا'),
        ('Carpet', 'سجادة'), ('Bridge', 'جسر'), ('Bicycle', 'دراجة'), ('Rocket', 'صاروخ'),
        ('Compass', 'بوصلة'), ('Scissors', 'مقص'), ('Bottle', 'زجاجة'), ('Balloon', 'بالون'),
        ('Ladder', 'سلم'), ('Guitar', 'غيتار'), ('Basket', 'سلة'), ('Piano', 'بيانو'),
    ],
}
