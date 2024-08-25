### импорты библиотек ###
from mysql.connector import MySQLConnection
from PIL import Image, ImageDraw
import wx, copy, threading, os
### импорты библиотек ###

### настройки базы ###
host = '127.0.0.1'
user = 'root'
passwd = ''
db = 'vegindex'
### настройки базы ###

### для расчётов ###
def NDVI_calc(NIR, RED):
    if (NIR + RED == 0):
        return NIR - RED
    else:
        return (NIR - RED) / (NIR + RED)

def VARI_calc(RED, GREEN, BLUE):
    if (GREEN + RED - BLUE != 0):
        return (GREEN - RED) / (GREEN + RED - BLUE)
    else:
        return (GREEN - RED)
### для расчётов ###

### запросы к базе ###    
def request(conn, text):
    cursor = conn.cursor()
    cursor.execute(text)
    data = cursor.fetchall()
    return data

### для работы с файлами ###
def read_file(filename):
    with open(filename, 'rb') as f:
        photo = f.read()
    return photo

def write_file(data, filename):
    with open(filename, 'wb') as f:
        f.write(data)
### для работы с файлами ###

### подключение к базе        
conn = MySQLConnection(host=host, user=user, passwd=passwd, db=db)
username = ''

### форма авторизации ###
class Auth ( wx.Dialog ):
  ### объявление всех элементов формы авторизации ###
  def __init__( self, parent ):
    wx.Dialog.__init__ ( self, parent, wx.ID_ANY, title = u"Система Авторизации", pos = wx.DefaultPosition, size = wx.Size( 294,168 ), style = wx.DEFAULT_DIALOG_STYLE )
    self.SetSizeHints( wx.DefaultSize, wx.DefaultSize );gSizer1 = wx.GridSizer( 0, 2, 0, 0 )    
    self.State_Label = wx.StaticText( self, wx.ID_ANY, u"Состояние", wx.DefaultPosition, wx.DefaultSize, 0 );self.State_Label.Wrap( -1 );gSizer1.Add( self.State_Label, 0, wx.ALL|wx.ALIGN_BOTTOM|wx.ALIGN_CENTER_HORIZONTAL, 5 )
    self.State_Value = wx.StaticText( self, wx.ID_ANY, u"Ожидание", wx.DefaultPosition, wx.DefaultSize, 0 );self.State_Value.Wrap( 10 );gSizer1.Add( self.State_Value, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_BOTTOM, 5 )
    self.Login_Label = wx.StaticText( self, wx.ID_ANY, u"Логин", wx.DefaultPosition, wx.DefaultSize, 0 );self.Login_Label.Wrap( -1 );gSizer1.Add( self.Login_Label, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL, 5 )
    self.Login_Value = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 );gSizer1.Add( self.Login_Value, 0, wx.ALL|wx.EXPAND, 5 );self.Password_Label = wx.StaticText( self, wx.ID_ANY, u"Пароль", wx.DefaultPosition, wx.DefaultSize, 0 );self.Password_Label.Wrap( -1 );gSizer1.Add( self.Password_Label, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 5 )
    self.Password_Value = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 );gSizer1.Add( self.Password_Value, 0, wx.ALL|wx.EXPAND, 5 );self.Authentication = wx.Button( self, wx.ID_ANY, u"Войти", wx.DefaultPosition, wx.DefaultSize, 0 );gSizer1.Add( self.Authentication, 0, wx.ALL|wx.EXPAND, 5 )
    self.m_button2 = wx.Button( self, wx.ID_ANY, u"Зарегистрироваться", wx.DefaultPosition, wx.DefaultSize, 0 );gSizer1.Add( self.m_button2, 0, wx.ALL|wx.EXPAND, 5 )
    self.SetSizer( gSizer1 );self.Layout();self.Centre( wx.BOTH )
    self.Authentication.Bind( wx.EVT_BUTTON, self.Auth )
    self.m_button2.Bind( wx.EVT_BUTTON, self.Register )
    self.logged_in = False
  def __del__( self ):
    pass

  ### сама авторизация ###
  def Auth( self, event ):
    global username
    try:
        username = self.Login_Value.GetValue()
        if "'" in username: username = username[:username.index("'")]
        password = self.Password_Value.GetValue()
        if "'" in password: password = password[:password.index("'")]
        user = request(conn,'select * from users where username = '+repr(username)+' and password = '+repr(password)+';')
        if len(user) == 1:
            username = username
            self.logged_in = True
            self.State_Value.SetLabel('Успех!')
            self.Close()
        else: self.State_Value.SetLabel('Ошибка!')
    except Exception as e:
        print(e)
        self.State_Value.SetLabel('Ошибка!')

  ### регистрация пользователя ###
  def Register( self, event ):
    global username
    try:
        username = self.Login_Value.GetValue()
        if "'" in username: username = username[:username.index("'")]
        password = self.Password_Value.GetValue()
        if "'" in password: password = password[:password.index("'")]
        user = request(conn,'insert into users (username,password) values('+repr(username)+','+repr(password)+');')
        conn.commit()
        username = username
        self.logged_in = True
        self.State_Value.SetLabel('Успех!')
        self.Close()
    except Exception as e:
        print(e)
        self.State_Value.SetLabel('Ошибка!')

### основная форма ###
class Main ( wx.Frame ):
  ### объявление всех элементов основной формы ###
  def __init__( self, parent ):
    wx.Frame.__init__ ( self, parent, pos = wx.DefaultPosition, size = wx.Size( 1100,450 ), style = wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL )    
    self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )    
    self.fgSizer2 = wx.FlexGridSizer( 0, 4, 0, 0 );self.fgSizer2.SetFlexibleDirection( wx.BOTH );self.fgSizer2.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )    
    SelectChoices = [];self.Select = wx.ComboBox( self, wx.ID_ANY, u"1", wx.DefaultPosition, wx.DefaultSize, SelectChoices, 0 );self.Select.SetSelection( 0 );self.fgSizer2.Add( self.Select, 0, wx.ALL|wx.EXPAND, 5 )    
    self.NDVI = wx.Button( self, wx.ID_ANY, u"Обработка NDVI", wx.DefaultPosition, wx.DefaultSize, 0 );self.fgSizer2.Add( self.NDVI, 0, wx.ALL, 5 )    
    self.VARI = wx.Button( self, wx.ID_ANY, u"Обработка VARI", wx.DefaultPosition, wx.DefaultSize, 0 );self.fgSizer2.Add( self.VARI, 0, wx.ALL, 5 )    
    self.fgSizer2.AddSpacer(1);self.m_staticText8 = wx.StaticText( self, wx.ID_ANY, u"Оригинал:", wx.DefaultPosition, wx.DefaultSize, 0 ); self.m_staticText8.Wrap( -1 ); self.fgSizer2.Add( self.m_staticText8, 0, wx.ALL, 5 )
    self.Load = wx.Button( self, wx.ID_ANY, u"Загрузить Файл", wx.DefaultPosition, wx.DefaultSize, 0 );self.fgSizer2.Add( self.Load, 0, wx.ALL, 5 )    
    self.m_staticText9 = wx.StaticText( self, wx.ID_ANY, u"Обработка:", wx.DefaultPosition, wx.DefaultSize, 0 );self.m_staticText9.Wrap( -1 );self.fgSizer2.Add( self.m_staticText9, 0, wx.ALL, 5 )    
    self.fgSizer2.AddSpacer(1);self.Original = wx.StaticBitmap( self, wx.ID_ANY, wx.NullBitmap, wx.DefaultPosition, wx.DefaultSize, 0 );self.fgSizer2.Add( self.Original, 0, wx.ALL, 5 );
    self.fgSizer2.AddSpacer(1);self.Calculated = wx.StaticBitmap( self, wx.ID_ANY, wx.NullBitmap, wx.DefaultPosition, wx.DefaultSize, 0 );self.fgSizer2.Add( self.Calculated, 0, wx.ALL, 5 )
    self.Legend = wx.StaticBitmap( self, wx.ID_ANY, wx.NullBitmap, wx.DefaultPosition, wx.DefaultSize, 0 );self.fgSizer2.Add( self.Legend, 0, wx.ALL, 5 )
    self.m_gauge1 = wx.Gauge( self, wx.ID_ANY, 100, wx.DefaultPosition, wx.DefaultSize, wx.GA_HORIZONTAL );self.m_gauge1.SetValue( 0 ) ;self.fgSizer2.Add( self.m_gauge1, 0, wx.ALL, 5 )    
    self.fgSizer2.AddSpacer(1);self.m_staticText10 = wx.StaticText( self, wx.ID_ANY, u"Процент плохой растительности", wx.DefaultPosition, wx.DefaultSize, 0 );self.m_staticText10.Wrap( -1 );self.fgSizer2.Add( self.m_staticText10, 0, wx.ALL, 5 )    
    self.Calc_Result = wx.StaticText( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 );self.Calc_Result.Wrap( -1 );self.fgSizer2.Add( self.Calc_Result, 0, wx.ALL, 5 )
    self.SetSizer( self.fgSizer2 );self.Layout();self.Centre( wx.BOTH )
    self.Select.Bind( wx.EVT_COMBOBOX, self.Select_picture )
    self.Load.Bind( wx.EVT_BUTTON, self.Load_picture )
    self.NDVI.Bind( wx.EVT_BUTTON, self.NDVI_calculation )
    self.VARI.Bind( wx.EVT_BUTTON, self.VARI_calculation )

    ### открываем форму авторизации и ждём ###
    dlg = Auth(self)
    dlg.ShowModal()

    authenticated = dlg.logged_in

    ### если не прошли авторизацию - выходим ###
    if not authenticated:
        self.Close()
    else:
        ### работа с пользователем ###
        global username
        self.user = username
        self.piname = ''
        ### загружаем список изображений из базы для нашего пользователя
        self.Select.Clear()
        images = request(conn,'select iname from pictures where username = '+repr(username)+';')
        for i in list(images):
            self.Select.Append(str(i[0]))
        ### объявляем общие переменные для работы ###
        self.original_pic = None
        self.ndvi_pic = None
        self.vari_pic = None
        self.ndvi_perc = 0
        self.vari_perc = 0
        ### показываем основную форму ###
        self.Show()
  def __del__( self ):
    pass

  ### если выбрали из списка, подгружаем из базы ###
  def Select_picture( self, event ):
    self.piname = self.Select.GetValue()
    query = "SELECT pic_original FROM pictures WHERE username = "+repr(self.user)+" and iname = " + repr(self.Select.GetValue())
    cursor = conn.cursor()
    cursor.execute(query)
    photo = cursor.fetchone()[0]
    write_file(photo, self.piname) ### сохраняем в файл
    start_image = wx.Image(self.piname) ### загружаем из файла для формы
    start_image.Rescale(350, 300) ### изменяем размер ###
    image = wx.Bitmap(start_image) 
    self.original_pic = Image.open(self.piname).convert("RGB") ### загружаем для работы ###
    self.Original.SetBitmap(image) ### показываем изображение
    ### убираем старое изображение с расчётами
    self.Legend.Hide()
    self.Calculated.Hide() 
    self.Calc_Result.SetLabel("")
    ### получаем из базы ndvi ###
    query = "SELECT pic_ndvi,percent_ndvi FROM pictures WHERE username = "+repr(self.user)+" and iname = " + repr(self.Select.GetValue())
    cursor = conn.cursor()
    cursor.execute(query)
    photo, self.ndvi_perc = cursor.fetchone()
    ### если нашли в базе ndvi - загружаем в память ###
    try:
        write_file(photo, self.piname + '_NDVI.jpg')
        start_image = wx.Image(self.piname + '_NDVI.jpg') 
        start_image.Rescale(350, 300) 
        self.ndvi_pic = wx.Bitmap(start_image)
    except: pass

    ### получаем из базы vari ###
    query = "SELECT pic_vari,percent_vari FROM pictures WHERE username = "+repr(self.user)+" and iname = " + repr(self.Select.GetValue())
    cursor = conn.cursor()
    cursor.execute(query)
    photo, self.vari_perc = cursor.fetchone()
    ### если нашли в базе vari - загружаем в память ###
    try:
        write_file(photo, self.piname + '_VARI.jpg')
        start_image = wx.Image(self.piname + '_VARI.jpg') 
        start_image.Rescale(350, 300) 
        self.vari_pic = wx.Bitmap(start_image)
    except: pass
    self.Layout()
    
  def Load_picture( self, event ):
    ### запрашиваем у пользователя путь к файлу с изображением ###
    openFileDialog = wx.FileDialog(self, "Open", "", "", 
      "Image files (*.jpg,*)|*.jpg", 
       wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
    openFileDialog.ShowModal()
    ### если пользователь выбрал файл, продолжаем ###
    try:
        ### открываем фото и загружаем для формы
        temp = openFileDialog.GetPath()
        start_image = wx.Image(temp) 
        start_image.Rescale(350, 300) ### изменяем размер
        image = wx.Bitmap(start_image)  
        self.original_pic = Image.open(temp).convert("RGB") ### загружаем в память для работы
        self.Original.SetBitmap(image) ### загружаем на форму 
        
        data = read_file(temp) ### загружаем в память для отгрузки в базу
        cursor = conn.cursor()
        sql = "INSERT INTO pictures(iname,username,pic_original) VALUES ("+repr(os.path.basename(temp))+","+repr(self.user)+",%s);"
        cursor.execute(sql, (data,)) ### отправляем в базу ###
        conn.commit() ### сохраняем изменения ###
        self.piname = os.path.basename(temp) ### запоминаем идентификатор нового фото
        ### переобъявляем значения для общих переменных
        self.ndvi_pic = None
        self.vari_pic = None
        self.ndvi_perc = 0
        self.vari_perc = 0
        ### убираем старое изображение и расчёты
        self.Legend.Hide()
        self.Calculated.Hide()
        self.Calc_Result.SetLabel("")
        ### перезагружаем список с изображениями из базы
        self.Select.Clear()
        images = request(conn,'select iname from pictures where username = '+repr(username)+';')
        for i in list(images):
            self.Select.Append(str(i[0]))
        ### выделяем текущее новое изображение в списке ###
        self.Select.SetValue(os.path.basename(temp))
        self.Layout()
    except: pass
  
  def NDVI_calculation( self, event ):
    def callback():
        if self.ndvi_pic == None:
            self.m_gauge1.SetValue( 0 ) ### обнуляем счётчик загрузки
            b = 0 ### обнуляем счётчик для расчётов
            orig = copy.copy(self.original_pic) ### делаем копию изначального изображения
            draw = ImageDraw.Draw(orig) ### подготавливаем фото для изменений
            width = self.original_pic.size[0]  # Определяем ширину.
            height = self.original_pic.size[1]  # Определяем высоту.
            pix = orig.load() ### загружаем фото в память
            mas = []
            mx = width * height ### расчитываем кол-во итераций
            self.m_gauge1.SetRange( mx*2 ) ### настраиваем счётчик загрузки
            for i in range(width):
                mas.append([])
                for j in range(height):
                    RED = pix[i, j][0]
                    NIR = pix[i, j][1]
                    mas[i].append(NDVI_calc(NIR, RED)) ### проводим расчёты
                    self.m_gauge1.SetValue( width*height ) ### обновляем счётчик загрузки
            for i in range(width):
                for j in range(height):
                    if (mas[i][j] <= 0.0025):
                        draw.point((i, j), (0, 0, 0)) ### изменяем фото
                        b += 1 ### добавляем значение в счётчике
                    elif (mas[i][j] > 0.025 and mas[i][j] < 0.3): draw.point((i, j), (244, 244, 0)) ### изменяем фото
                    else: draw.point((i, j), (0, 255, 0)) ### изменяем фото
                    self.m_gauge1.SetValue( mx + width*height ) ### обновляем счётчик загрузки
            orig.save(self.piname + "_NDVI.jpg", "JPEG", quality=100, optimize=True, progressive=True) ### сохраняем изображение после обработки
            start_image = wx.Image(self.piname + "_NDVI.jpg") ### загружаем изображение для формы
            start_image.Rescale(350, 300) ### изменяем размер
            image = wx.Bitmap(start_image)
            self.ndvi_pic = image
            self.Calculated.SetBitmap(image) ### показываем фото после расчётов
            s = round((b * 100) / (width * height),5) ### приведение результатов к процентному виду
            data = read_file(self.piname + "_NDVI.jpg") ### загружаем фото для базы
            cursor = conn.cursor()
            sql = "UPDATE pictures SET pic_ndvi = %s where iname = "+repr(self.piname)+" and username = "+repr(self.user)+";"
            cursor.execute(sql, (data,)) ### отправляем фото в базу
            sql = "UPDATE pictures SET percent_ndvi = %s where iname = "+repr(self.piname)+" and username = "+repr(self.user)+";"
            cursor.execute(sql, (s,)) ### отправляем результаты в базу
            conn.commit() ### сохраняем изменения в базе
            self.Calc_Result.SetLabel(str(s) + "%") ### показываем результаты на форме
        else:
            self.Calculated.SetBitmap(self.ndvi_pic) ### загружаем на форму готовое изображение
            self.Calc_Result.SetLabel(str(self.ndvi_perc) + "%") ### загружаем на форму готовые результаты
        start_image = wx.Image("ndvi") ### загружаем изображение для формы
        start_image.Rescale(200, 200) ### изменяем размер
        image = wx.Bitmap(start_image) 
        self.Legend.SetBitmap(image)
        self.Legend.Show()
        self.Calculated.Show() 
        self.Layout()
    ### проводим все расчёты в фоне ###
    t = threading.Thread(target=callback)
    t.start()
    
  def VARI_calculation( self, event ):
    def callback():
        if self.vari_pic == None:
            self.m_gauge1.SetValue( 0 ) ### обнуляем счётчик загрузки
            b = 0 ### обнуляем счётчик для расчётов
            orig = copy.copy(self.original_pic) ### делаем копию изначального изображения
            draw = ImageDraw.Draw(orig) ### подготавливаем фото для изменений
            width = self.original_pic.size[0]  # Определяем ширину.
            height = self.original_pic.size[1]  # Определяем высоту.
            pix = orig.load() ### загружаем фото в память
            mas = []
            mx = width * height ### расчитываем кол-во итераций
            self.m_gauge1.SetRange( mx*2 ) ### настраиваем счётчик загрузки
            for i in range(width):
                mas.append([])
                for j in range(height):
                    RED = pix[i, j][0]
                    GREEN = pix[i, j][1]
                    BLUE = pix[i, j][2]
                    mas[i].append(VARI_calc(RED, GREEN, BLUE)) ### проводим расчёты
                    self.m_gauge1.SetValue( width*height ) ### обновляем счётчик загрузки
            for i in range(width):
                for j in range(height):
                    if (mas[i][j] <= 0): draw.point((i, j), (0, 0, 0)) ### изменяем фото
                    elif (mas[i][j] < 0.1):
                        draw.point((i, j), (255, 0, 0)) ### изменяем фото
                        b += 1
                    elif (mas[i][j] < 0.2): draw.point((i, j), (244, 251, 0)) ### изменяем фото
                    else: draw.point((i, j), (0, 255, 0)) ### изменяем фото
                    self.m_gauge1.SetValue( mx + width*height ) ### обновляем счётчик загрузки
                    
            orig.save(self.piname + "_VARI.jpg", "JPEG", quality=100, optimize=True, progressive=True) ### сохраняем изображение после обработки
            start_image = wx.Image(self.piname + "_VARI.jpg") ### загружаем изображение для формы
            start_image.Rescale(350, 300) ### изменяем размер
            image = wx.Bitmap(start_image)
            self.vari_pic = image
            self.Calculated.SetBitmap(image) ### показываем фото после расчётов
            s = round((b * 100) / (width * height),5) ### приведение результатов к процентному виду
            data = read_file(self.piname + "_VARI.jpg") ### загружаем фото для базы
            cursor = conn.cursor()
            sql = "UPDATE pictures SET pic_vari = %s where iname = "+repr(self.piname)+" and username = "+repr(self.user)+";"
            cursor.execute(sql, (data,)) ### отправляем фото в базу
            sql = "UPDATE pictures SET percent_vari = %s where iname = "+repr(self.piname)+" and username = "+repr(self.user)+";"
            cursor.execute(sql, (s,)) ### отправляем результаты в базу
            conn.commit() ### сохраняем изменения в базе
            self.Calc_Result.SetLabel(str(s) + "%") ### показываем результаты на форме
        else:
            self.Calculated.SetBitmap(self.vari_pic) ### загружаем на форму готовое изображение
            self.Calc_Result.SetLabel(str(self.vari_perc) + "%") ### загружаем на форму готовые результаты
        start_image = wx.Image("vari") ### загружаем изображение для формы
        start_image.Rescale(200, 200) ### изменяем размер
        image = wx.Bitmap(start_image) 
        self.Legend.SetBitmap(image)
        self.Legend.Show()
        self.Calculated.Show() 
        self.Layout()
    ### проводим все расчёты в фоне ###
    t = threading.Thread(target=callback)
    t.start()
### запускаем графическую оболочку программы ###
app = wx.App(False)
frame = Main(None)
app.MainLoop()
### запускаем графическую оболочку программы ###
