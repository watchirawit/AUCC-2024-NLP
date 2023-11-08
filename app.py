from flask import Flask, render_template, request, redirect, url_for, flash,jsonify
from flask_login import current_user
from pythainlp.tokenize import word_tokenize
from pythainlp.tag import pos_tag
from pythainlp.util import collate
from pythainlp.translate import Translate
import json



from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user


app = Flask(__name__)

app.config['SECRET_KEY'] = 'boss'  # Replace with a secure secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost/nlp'  # Replace with your MySQL connection string
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    saved_words = db.relationship('SavedWord', backref='user', lazy=True)


class SavedWord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    thai_word = db.Column(db.String(100), nullable=False)
    english_translation = db.Column(db.String(100), nullable=False)
    pos = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    


def translate_word(word):
    translator = Translate('th', 'en')
    return translator.translate(word)
def translate_text(text_to_translate):
    words = word_tokenize(text_to_translate, engine="attacut", keep_whitespace=False)
    translated_words = [translate_word(word) for word in words]
    return " ".join(translated_words)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash('You have been logged in!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Login failed. Please check your username and password.', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/my_vocabulary/<pos_type>')
@login_required
def my_vocabulary_by_pos(pos_type):
    tes = dict()
    words = dict()
    user_id = current_user.id
    saved_words = SavedWord.query.filter_by(user_id=user_id, pos=pos_type).all()
    thai = []
    eng = []
    eng_sord = []
    
    for word in saved_words:
        print(word.thai_word)
        print(word.english_translation)
        thai.append(word.thai_word)
        eng.append(word.english_translation)
    sord_thai = collate(thai)
    print(thai)
    print(eng)
    print(sord_thai)
    for indexs,thai_word in enumerate(thai):
        tes[sord_thai.index(thai_word)] = eng[indexs]

    print(tes)
    

    sorted_dict = dict(sorted(tes.items()))
    #saved_words.sort(key=lambda word: collate(word.thai_word))
    for val in sorted_dict.values():
        eng_sord.append(val)
    
    for indexs,val in enumerate(eng_sord):
        words[sord_thai[indexs]] = val
    print(sorted_dict)
    print(words)

    return render_template('my_vocabulary_by_pos.html', words=words, pos_type=pos_type)




@app.route('/save_word', methods=['POST'])
@login_required
def save_word():
    data = request.get_json()
    thai_word = data.get('thai_word')
    english_translation = data.get('english_translation')
    pos = data.get('pos')

    if thai_word and english_translation and pos:
        saved_word = SavedWord(
            thai_word=thai_word,
            english_translation=english_translation,
            pos=pos,
            user=current_user
        )
        db.session.add(saved_word)
        db.session.commit()
        return jsonify({'success': True})
    else:
        return jsonify({'success': False})


# Add this import at the top of your app.py
  # Adjust the import as needed

# Update the route for my_vocabulary
@app.route('/my_vocabulary', methods=['GET'])
@login_required
def my_vocabulary():
    pos_types = ["NOUN", "VERB", "ADJ", "ADP", "PROPN", "SCONJ", "PRON", "PART", "ADV", "AUX", "DET", "CCONJ"]
    
    last_words_by_pos = {}
    for pos_type in pos_types:
        # Query the database to retrieve the last 3 recorded words for each POS
        last_words = SavedWord.query.filter_by(user_id=current_user.id, pos=pos_type).order_by(SavedWord.id.desc()).limit(3).all()
        last_words_by_pos[pos_type] = last_words

    return render_template('my_vocabulary.html', pos_types=pos_types, recent_words=last_words_by_pos)


# @app.route("/", methods=["GET", "POST"])
@app.route('/index', methods=['GET', 'POST'])
@login_required

def index():
    tagged_text = ""
    filtered_tags = []
    translations = {}
    thai_pro = ['เชียงใหม่', 'เชียงราย', 'ลำปาง', 'ลำพูน', 'แม่ฮ่องสอน', 'น่าน', 'พะเยา', 'อุตรดิตถ์', 'กาฬสินธุ์', 'ขอนแก่น', 'ชัยภูมิ', 'นครพนม', 'นครราชสีมา', 'บึงกาฬ', 'บุรีรัมย์', 'มหาสารคาม', 'มุกดาหาร', 'ยโสธร', 'ร้อยเอ็ด', 'สกลนคร', 'สุรินทร์', 'ศรีสะเกษ', 'หนองคาย', 'หนองบัวลำภู', 'อุดรธานี', 'อุบลราชธานี', 'อำนาจเจริญ', 'กรุงเทพมหานคร', 'กำแพงเพชร', 'ชัยนาท', 'นครนายก', 'นครปฐม', 'นครสวรรค์', 'นนทบุรี', 'ปทุมธานี', 'พระนครศรีอยุธยา', 'พิจิตร', 'พิษณุโลก', 'เพชรบูรณ์', 'ลพบุรี', 'สมุทรปราการ', 'สมุทรสงคราม', 'สมุทรสาคร', 'สิงห์บุรี', 'สุโขทัย', 'สุพรรณบุรี', 'สระบุรี', 'อุทัยธานี', 'จันทบุรี', 'ฉะเชิงเทรา', 'ชลบุรี', 'ตราด', 'ปราจีนบุรี', 'ระยอง', 'สระแก้ว', 'กาญจนบุรี', 'ประจวบคีรีขันธ์', 'เพชรบุรี', 'ราชบุรี', 'ชุมพร', 'ตรัง', 'นครศรีธรรมราช', 'นราธิวาส', 'ปัตตานี', 'พังงา', 'พัทลุง', 'ภูเก็ต', 'ระนอง', 'สตูล', 'สงขลา', 'สุราษฎร์ธานี', 'ยะลา']
    eng_pro = ['Chiang Mai', 'Chiang Rai', 'Lampang', 'Lamphun', 'Mae Hong Son', 'Nan', 'Phayao', 'Uttaradit', 'Kalasin', 'Khon Kaen', 'Chaiyaphum', 'Nakhon Phanom', 'Nakhon Ratchasima', 'Bueng Kan', 'Buriram', 'Maha Sarakham', 'Mukdahan', 'Yasothon', 'Roi Et',  'Sakon Nakhon', 'Surin', 'Sisaket', 'Nong Khai', 'Nong Bua Lamphu', 'Udon Thani', 'Ubon Ratchathani', 'Amnat Charoen', 'Bangkok', 'Kamphaeng Phet', 'Chai Nat', 'Nakhon Nayok', 'Nakhon Pathom', 'Nakhon Sawan', 'Nonthaburi', 'Pathum Thani', 'Phra Nakhon Si Ayutthaya', 'Phichit', 'Phitsanulok', 'Phetchabun', 'Lopburi', 'Samut Prakan', 'Samut Songkhram', 'Samut Sakhon', 'Sing Buri', 'Sukhothai', 'Suphan Buri', 'Saraburi', 'Uthai Thani', 'Chanthaburi', 'Chachoengsao', 'Chonburi', 'Trat', 'Prachinburi', 'Rayong', 'Sa Kaeo', 'Kanchanaburi', 'Prachuap Khiri Khan', 'Phetchaburi', 'Ratchaburi', 'Chumphon', 'Trang', 'Nakhon Si Thammarat', 'Narathiwat', 'Pattani', 'Phang Nga', 'Phatthalung', 'Phuket', 'Ranong', 'Satun', 'Songkhla', 'Surat Thani', 'Yala']

    if request.method == "POST":
        input_text = request.form["input_text"]

        word_tokenize_thai = word_tokenize(input_text, engine="attacut", keep_whitespace=False)
          # Translate the entire text
        
        translated_text = []
        for word in word_tokenize_thai:
            if word in thai_pro:
                translated_text.append(eng_pro[thai_pro.index(word)])
            else:
                translated_text.append(translate_word(word))

        # Populate the translations dictionary with Thai words as keys and translations as values
        translations = {word: translated_text[indexs] for indexs,word in enumerate(word_tokenize_thai)}
        print('translations',translations)

        tag_pos = pos_tag(word_tokenize_thai, corpus="orchid_ud")

        selected_tags = request.form.getlist("pos_tags")
        filtered_tags = set(selected_tags)

        tagged_text = highlight_pos_tags(translated_text, word_tokenize_thai, tag_pos, filtered_tags)
   

    return render_template("index.html", tagged_text=tagged_text, filtered_tags=filtered_tags, translations=json.dumps(translations))

def highlight_pos_tags(translated_text, words, tags, filtered_tags=None):
    result = ""
 
    translations = dict(zip(words, translated_text))

    for word, tag in zip(words, tags):
        if filtered_tags is None or tag[1] in filtered_tags:
            translation = translations.get(word, "")
            # Add a span for the highlighted word, a save button, and data attributes for Thai and English words and POS
            result += f'<span class="{tag[1]}" title="{translation}">{word}</span> '
            result += f'<button class="save-button" ' \
                      f'data-thai-word="{word}" ' \
                      f'data-english-translation="{translation}" ' \
                      f'data-pos="{tag[1]}" ' \
                      f'onclick="saveWord(this)">Save</button>'
        else:
            result += f'{word} '

    return result

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
