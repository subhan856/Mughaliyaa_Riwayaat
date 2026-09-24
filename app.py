import os, sqlite3, secrets
from urllib.parse import quote
import streamlit as st

st.set_page_config(page_title='Mughaliyaa Riyawaat', page_icon='👑', layout='wide')
DB='mughaliyaa.db'
STORE_NAME=os.getenv('STORE_NAME','Mughaliyaa Riyawaat')
PHONE=os.getenv('STORE_PHONE','+923333482225')
WA=os.getenv('STORE_WHATSAPP',PHONE)
EMAIL=os.getenv('STORE_EMAIL','mughaliyaariwayaat72@gmail.com')
ADDRESS=os.getenv('STORE_ADDRESS','Rawalpindi, Pakistan')
ADMIN_PHONE=os.getenv('ADMIN_PHONE',PHONE)

st.markdown('''<style>
.stApp{background:#f7f1e6;color:#18352d}.block-container{max-width:1200px;padding-top:1rem}
.top{background:#18352d;color:#f3d58a;padding:18px;text-align:center;border-radius:5px;margin-bottom:20px}
.brand{font:700 28px Georgia;letter-spacing:2px}.hero{padding:60px 35px;border:1px solid #e5d6b9;border-radius:8px;background:linear-gradient(135deg,#efe3cc,#fffaf1);margin-bottom:25px}
.hero h1{font:55px Georgia;line-height:1.02;color:#18352d}.hero small{color:#9a6c19;letter-spacing:3px}.hero p{font:17px Arial;color:#5d665f;max-width:650px;line-height:1.6}
.price{color:#9a6c19;font-weight:700;font-size:18px}.old{text-decoration:line-through;color:#888}.feature{background:#18352d;color:#f3d58a;padding:20px;text-align:center;border-radius:5px;font-weight:600}.foot{background:#122a24;color:#e9ddc4;padding:30px;text-align:center;border-radius:5px;margin-top:30px}
</style>''',unsafe_allow_html=True)

def conn(): return sqlite3.connect(DB,check_same_thread=False)
def init():
    c=conn(); x=c.cursor()
    x.execute('CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT,phone TEXT UNIQUE,name TEXT,email TEXT,is_admin INTEGER DEFAULT 0)')
    x.execute('CREATE TABLE IF NOT EXISTS products(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT,category TEXT,description TEXT,price REAL,sale_price REAL,stock INTEGER,image TEXT,sizes TEXT,colors TEXT,active INTEGER DEFAULT 1,featured INTEGER DEFAULT 0)')
    x.execute('CREATE TABLE IF NOT EXISTS orders(id INTEGER PRIMARY KEY AUTOINCREMENT,order_no TEXT UNIQUE,user_id INTEGER,customer_name TEXT,phone TEXT,address TEXT,payment_method TEXT,total REAL,status TEXT DEFAULT "Pending",tracking_code TEXT DEFAULT "",created_at TEXT DEFAULT CURRENT_TIMESTAMP)')
    x.execute('CREATE TABLE IF NOT EXISTS order_items(id INTEGER PRIMARY KEY AUTOINCREMENT,order_id INTEGER,product_id INTEGER,product_name TEXT,qty INTEGER,price REAL,size TEXT,color TEXT)')
    x.execute('CREATE TABLE IF NOT EXISTS coupons(code TEXT PRIMARY KEY,percent REAL,active INTEGER DEFAULT 1)')
    if x.execute('SELECT COUNT(*) FROM products').fetchone()[0]==0:
        data=[
        ('Royal Bridal Lehenga','Bridal','Luxury bridal lehenga.',85000,75000,6,'https://images.unsplash.com/photo-1594633312681-425c7b97ccd1','S,M,L,XL','Maroon,Gold'),
        ('Mughal Sharara','Sharara','Elegant festive sharara.',48500,None,8,'https://images.unsplash.com/photo-1610030469983-98e550d080f1','S,M,L,XL','Red,Gold'),
        ('Emerald Formal','Formal','Royal emerald formal wear.',32000,None,10,'https://images.unsplash.com/photo-1595777457583-95e059d581b8','S,M,L,XL','Emerald,Black'),
        ('Velvet Evening Dress','Party Wear','Velvet evening outfit.',27500,24500,12,'https://images.unsplash.com/photo-1566479179817-c0e1f2c7f6f3','S,M,L,XL','Black,Maroon')]
        x.executemany('INSERT INTO products(name,category,description,price,sale_price,stock,image,sizes,colors,featured) VALUES(?,?,?,?,?,?,?,?,?,1)',data)
    x.execute('INSERT OR IGNORE INTO coupons VALUES("ROYAL10",10,1)')
    x.execute('INSERT OR IGNORE INTO users(phone,name,email,is_admin) VALUES(?,?,?,1)',(ADMIN_PHONE,'Store Admin',os.getenv('ADMIN_EMAIL','bsubhan800@gmail.com')))
    c.commit(); c.close()
init()

def rows(sql,p=()):
    c=conn(); r=c.execute(sql,p).fetchall(); c.close(); return r
def one(sql,p=()):
    r=rows(sql,p); return r[0] if r else None
def run(sql,p=()):
    c=conn(); c.execute(sql,p); c.commit(); c.close()
def price(p): return float(p[5] if p[5] is not None else p[4])
def money(n): return f'PKR {n:,.0f}'
def wa(msg): return 'https://wa.me/'+WA.replace('+','').replace(' ','')+'?text='+quote(msg)

for k,v in {'page':'Home','cart':{},'user':None,'otp':'','pending':'','selected':None}.items():
    if k not in st.session_state: st.session_state[k]=v

st.markdown(f'<div class="top"><div class="brand">MUGHALIYAA RIYAWAAT</div>THE ROYAL COLLECTION • BRIDAL • LEHENGA • SHARARA • FORMAL</div>',unsafe_allow_html=True)

pages=['Home','Shop','Cart','Login','My Orders','Track Order']
if st.session_state.user and st.session_state.user[3]: pages.append('Admin')
with st.sidebar:
    page=st.radio('Menu',pages,index=pages.index(st.session_state.page) if st.session_state.page in pages else 0)
    st.session_state.page=page
    st.write('🛒 Cart:',sum(x['qty'] for x in st.session_state.cart.values()))
    st.markdown(f'[💬 WhatsApp Support]({wa("Assalam o Alaikum, Mughaliyaa Riyawaat se maloomat chahiye.")})')
    st.caption(ADDRESS)

if page=='Home':
    st.markdown('<div class="hero"><small>THE ROYAL COLLECTION</small><h1>Tradition,<br>Reimagined.</h1><p>Luxury Pakistani fashion inspired by heritage, crafted for the modern woman.</p></div>',unsafe_allow_html=True)
    a,b,c=st.columns(3)
    for col,text in zip((a,b,c),('🔐 Secure Login','🚚 Order Tracking','💬 WhatsApp Support')):
        col.markdown(f'<div class="feature">{text}</div>',unsafe_allow_html=True)
    st.subheader('Featured Collection')
    ps=rows('SELECT * FROM products WHERE active=1 ORDER BY featured DESC,id DESC LIMIT 8')
    cols=st.columns(4)
    for i,p in enumerate(ps):
        with cols[i%4]:
            if p[7]: st.image(p[7],use_container_width=True)
            st.markdown(f'### {p[1]}')
            st.markdown(f'<span class="price">{money(price(p))}</span>',unsafe_allow_html=True)
            if st.button('View Product',key=f'h{i}'):
                st.session_state.selected=p[0]; st.session_state.page='Shop'; st.rerun()

elif page=='Shop':
    st.title('🛍️ Shop')
    search=st.text_input('Search','')
    cats=['All']+[x[0] for x in rows('SELECT DISTINCT category FROM products ORDER BY category')]
    cat=st.selectbox('Category',cats)
    if st.session_state.selected:
        p=one('SELECT * FROM products WHERE id=?',(st.session_state.selected,))
        if p:
            st.markdown('---'); a,b=st.columns(2)
            with a:
                if p[7]: st.image(p[7],use_container_width=True)
            with b:
                st.header(p[1]); st.write(p[3]); st.write('Category:',p[2]); st.markdown(f'### {money(price(p))}')
                sizes=[x.strip() for x in p[8].split(',') if x.strip()] or ['Standard']
                colors=[x.strip() for x in p[9].split(',') if x.strip()] or ['Default']
                size=st.selectbox('Size',sizes); color=st.selectbox('Color',colors); qty=st.number_input('Quantity',1,max(1,p[6]),1)
                if st.button('🛒 Add to Cart',type='primary'):
                    st.session_state.cart[str(p[0])]={'qty':int(qty),'size':size,'color':color}; st.success('Product cart mein add ho gaya.')
                if st.button('Back'): st.session_state.selected=None; st.rerun()
    ps=rows('SELECT * FROM products WHERE active=1 AND (name LIKE ? OR category LIKE ?) '+('AND category=? ' if cat!='All' else '')+'ORDER BY featured DESC,id DESC',([f'%{search}%',f'%{search}%']+([cat] if cat!='All' else [])))
    cols=st.columns(4)
    for i,p in enumerate(ps):
        with cols[i%4]:
            if p[7]: st.image(p[7],use_container_width=True)
            st.markdown(f'### {p[1]}'); st.markdown(f'**{money(price(p))}**')
            if st.button('View',key=f's{i}'): st.session_state.selected=p[0]; st.rerun()

elif page=='Cart':
    st.title('🛒 Your Cart')
    if not st.session_state.cart: st.info('Cart abhi empty hai.')
    else:
        total=0
        for pid,d in list(st.session_state.cart.items()):
            p=one('SELECT * FROM products WHERE id=?',(pid,))
            if not p: continue
            line=price(p)*d['qty']; total+=line
            a,b,c=st.columns([3,2,1]); a.write(f'**{p[1]}** ({d["size"]}/{d["color"]})'); b.write(f'{d["qty"]} × {money(price(p))}');
            if c.button('Remove',key=f'r{pid}'): st.session_state.cart.pop(pid); st.rerun()
        st.markdown(f'## Total: {money(total)}')
        if st.button('Proceed to Checkout',type='primary'):
            if not st.session_state.user: st.warning('Pehle Login karo.'); st.session_state.page='Login'; st.rerun()
            else: st.session_state.page='Checkout'; st.rerun()

elif page=='Checkout':
    if not st.session_state.user: st.session_state.page='Login'; st.rerun()
    st.title('📦 Checkout'); address=st.text_area('Delivery Address'); payment=st.selectbox('Payment Method',['Cash on Delivery (COD)','Bank Transfer']); coupon=st.text_input('Coupon').strip().upper()
    total=sum(price(one('SELECT * FROM products WHERE id=?',(pid,)))*d['qty'] for pid,d in st.session_state.cart.items() if one('SELECT * FROM products WHERE id=?',(pid,)))
    cp=one('SELECT percent FROM coupons WHERE code=? AND active=1',(coupon,)) if coupon else None
    final=total-(total*float(cp[0])/100 if cp else 0); st.markdown(f'### Payable: {money(final)}')
    if st.button('Place Order',type='primary'):
        if not address.strip(): st.error('Delivery address zaroori hai.')
        elif not st.session_state.cart: st.error('Cart empty hai.')
        else:
            no='MR-'+secrets.token_hex(5).upper(); u=st.session_state.user
            c=conn(); cur=c.cursor(); cur.execute('INSERT INTO orders(order_no,user_id,customer_name,phone,address,payment_method,total) VALUES(?,?,?,?,?,?,?)',(no,u[0],u[1] or 'Customer',u[2],address,payment,final)); oid=cur.lastrowid
            for pid,d in st.session_state.cart.items():
                p=one('SELECT * FROM products WHERE id=?',(pid,)); cur.execute('INSERT INTO order_items(order_id,product_id,product_name,qty,price,size,color) VALUES(?,?,?,?,?,?,?)',(oid,p[0],p[1],d['qty'],price(p),d['size'],d['color'])); cur.execute('UPDATE products SET stock=MAX(0,stock-?) WHERE id=?',(d['qty'],pid))
            c.commit(); c.close(); st.session_state.cart={}; st.success(f'Order place ho gaya: {no}'); st.markdown(f'[WhatsApp Order Support]({wa(f"Assalam o Alaikum, mera order {no} hai.")})')

elif page=='Login':
    st.title('🔐 Login')
    if st.session_state.user:
        st.success(f'Logged in: {st.session_state.user[1] or st.session_state.user[2]}')
        if st.button('Logout'): st.session_state.user=None; st.rerun()
    elif not st.session_state.pending:
        phone=st.text_input('Phone Number',placeholder='+923xxxxxxxxx')
        if st.button('Send OTP',type='primary') and phone.strip():
            st.session_state.pending=phone.strip().replace(' ',''); st.session_state.otp=f'{secrets.randbelow(1000000):06d}'; st.rerun()
    else:
        st.info(f'OTP sent for {st.session_state.pending}')
        st.warning(f'Demo OTP: {st.session_state.otp} — real SMS ke liye Twilio secrets add karo.')
        code=st.text_input('6-digit OTP',max_chars=6)
        name=st.text_input('Name')
        if st.button('Verify OTP',type='primary'):
            if code.strip()==st.session_state.otp:
                u=one('SELECT id,name,phone,is_admin FROM users WHERE phone=?',(st.session_state.pending,))
                if not u:
                    run('INSERT INTO users(phone,name,is_admin) VALUES(?,?,0)',(st.session_state.pending,name)); u=one('SELECT id,name,phone,is_admin FROM users WHERE phone=?',(st.session_state.pending,))
                elif name and not u[1]: run('UPDATE users SET name=? WHERE id=?',(name,u[0])); u=one('SELECT id,name,phone,is_admin FROM users WHERE phone=?',(st.session_state.pending,))
                st.session_state.user=u; st.session_state.pending=''; st.session_state.otp=''; st.rerun()
            else: st.error('OTP ghalat hai.')

elif page=='My Orders':
    st.title('📋 My Orders')
    if not st.session_state.user: st.warning('Pehle Login karo.')
    else:
        for o in rows('SELECT order_no,total,status,tracking_code,created_at FROM orders WHERE user_id=? ORDER BY id DESC',(st.session_state.user[0],)):
            st.write(f'**{o[0]}** — {money(o[1])} — {o[2]} — Tracking: {o[3] or "Not assigned"}')

elif page=='Track Order':
    st.title('🚚 Track Order'); code=st.text_input('Tracking Code')
    if st.button('Track'):
        o=one('SELECT order_no,status,created_at,tracking_code FROM orders WHERE tracking_code=?',(code.strip(),))
        if o: st.success(f'{o[0]} — {o[1]} — {o[3]}')
        else: st.error('Tracking code nahi mila.')

elif page=='Admin':
    if not st.session_state.user or not st.session_state.user[3]: st.error('Admin access required.')
    else:
        st.title('👑 Admin Dashboard'); t1,t2=st.tabs(['Products','Orders'])
        with t1:
            with st.form('add'):
                n=st.text_input('Product Name'); cat=st.selectbox('Category',['Bridal','Lehenga','Sharara','Formal','Party Wear','Other']); desc=st.text_area('Description'); pr=st.number_input('Price',0.0); sale=st.number_input('Sale Price (0=none)',0.0); stock=st.number_input('Stock',0,step=1); img=st.text_input('Image URL'); sizes=st.text_input('Sizes','S,M,L,XL'); colors=st.text_input('Colors','Black,Maroon,Gold'); ok=st.form_submit_button('Add Product')
            if ok and n: run('INSERT INTO products(name,category,description,price,sale_price,stock,image,sizes,colors,featured) VALUES(?,?,?,?,?,?,?,?,?,1)',(n,cat,desc,pr,sale or None,int(stock),img,sizes,colors)); st.success('Product add ho gaya.'); st.rerun()
            st.dataframe(rows('SELECT id,name,category,price,sale_price,stock FROM products ORDER BY id DESC'),use_container_width=True)
        with t2:
            for o in rows('SELECT id,order_no,customer_name,phone,total,status,tracking_code FROM orders ORDER BY id DESC'):
                st.write(f'**{o[1]}** | {o[2]} | {money(o[4])} | {o[5]} | {o[6] or "No tracking"}')

st.markdown(f'<div class="foot"><b>{STORE_NAME}</b><br><br>Bridal • Lehenga • Sharara • Formal • Party Wear<br><br>📞 {PHONE} | ✉️ {EMAIL}<br>{ADDRESS}<br><br>© 2026 Mughaliyaa Riyawaat</div>',unsafe_allow_html=True)
