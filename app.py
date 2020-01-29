import os
from flask import Flask, render_template, flash, request, redirect, url_for, session, Markup
import pandas as pd
from werkzeug.utils import secure_filename
import tablib

UPLOAD_FOLDER = 'static/'
ALLOWED_EXTENSIONS = set(['csv'])


app = Flask(__name__)
# Setting secret key for flask session
app.secret_key = b'unlock'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

#Checking if the uploaded file is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET','POST'])
def upload():
    filename = session.get('filename', None)
    if request.method == 'POST':
        if 'file' not in request.files:
            flash("No file part")
            return redirect(request.url)

        file = request.files['file']

        if file.filename == '':
            flash("No selected file")
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            #creating session of filename
            if filename:
                session["filename"] = filename

    return render_template('index.html', filename=filename)

@app.route('/csv', methods=['GET','POST'])
def csv(data=None, from_date=None, to_date=None):
    filename = session.get('filename', None)

    if request.method == 'POST':
        from_date = request.form['from']
        to_date = request.form['till']

    if not filename:
        return render_template('csv.html', data=data)

    if filename:
        df = pd.read_csv(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        #Converting pandas dataframe date column into convenient date format & type
        df['Date'] = pd.to_datetime(df['Date'], format='%d-%m-%y')
    if from_date and to_date:
        #Specifying date range for pandas data frame
        df = df.loc[(df['Date'] >= from_date) & (df['Date'] <= to_date)]
        
    dataset = tablib.Dataset()
    dataset.df = df
    return render_template('csv.html', data=Markup(dataset.html))

@app.route('/analyze', methods=['GET', 'POST'])
def analyze(number_list=None, number=None, analyze_type=None, from_date=None, to_date=None, 
most_frequent_contact=None, most_frequent_count=None, total_call_send=None, 
total_call_receive=None, top_ten_communicator=None, total_communicator=None, total_talk_time=None,
talk_time_list=None,receiver_list=None, top_talked_communicator=None, max_talk_num=None,
max_talk_time=None):
    filename = session.get('filename', None)

    if request.method == 'POST':
        number = request.form['number']
        
        analyze_type = request.form['type']
        from_date = request.form['from']
        to_date = request.form['till']

    if filename:
        df = pd.read_csv(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        #Converting pandas dataframe date column into convenient date format & type
        df['Date'] = pd.to_datetime(df['Date'], format='%d-%m-%y')

        #Converting pandas dataframe date column into convenient time format & type
        df['Start_time'] = pd.to_datetime(df['Start_time'], format="%I:%M:%S %p")
        df['End_time'] = pd.to_datetime(df['End_time'], format="%I:%M:%S %p")
        
        #Creating "talk_time" column
        df['talk_time'] = df['End_time'] - df['Start_time']

        #Creating unique user number from the data frame
        number_list = list(df["Caller"].unique())


    if from_date and to_date:
        #Specifying date range for pandas data frame
        df = df.loc[(df['Date'] >= from_date) & (df['Date'] <= to_date)]
        
    if analyze_type and number:
        most_frequent_contact = df[df['Caller'] == int(number)]['Receiver'].value_counts().keys().tolist()
        most_frequent_count = df[df['Caller'] == int(number)]['Receiver'].value_counts().tolist()
        total_call_send = sum(df[df['Caller'] == int(number)]['Receiver'].value_counts().tolist())
        total_call_receive = sum(df[df['Receiver'] == int(number)]['Caller'].value_counts().tolist())
        top_ten_communicator = zip(most_frequent_contact[:10], most_frequent_count[:10])
        total_communicator = len(most_frequent_contact)
        total_talk_time = df[df['Caller'] == int(number)]['talk_time'].sum().total_seconds()/3600

        #Creating receiver list
        receiver_list = df[df['Caller'] == int(number)]['Receiver'].unique().tolist()
        #Creating list of most_talked_contact
        talk_time_list = [df[df['Caller'] == int(number)][df['Receiver'] == num]['talk_time'].sum().total_seconds()/3600 for num in receiver_list]
        #Creating Most talked contact:talk time [Sorting]
        top_talked_communicator = sorted(zip(talk_time_list, receiver_list), reverse=True)

        receiver_list = [x for _,x in top_talked_communicator]
        talk_time_list = [x for x,_ in top_talked_communicator]

        max_talk_num = top_talked_communicator[0][1]
        max_talk_time = top_talked_communicator[0][0]

    return render_template('analyze.html', number_list = number_list, number=number,
        analyze_type=analyze_type, to_date=to_date, from_date=from_date, 
        most_frequent_contact=most_frequent_contact, most_frequent_count=most_frequent_count,
        total_call_send=total_call_send, total_call_receive=total_call_receive, 
        top_ten_communicator=top_ten_communicator, total_communicator=total_communicator,
        total_talk_time=total_talk_time, talk_time_list=talk_time_list, receiver_list=receiver_list,
        max_talk_num=max_talk_num, max_talk_time=max_talk_time, top_talked_communicator=top_talked_communicator)

if __name__ == "__main__":
    app.run(debug = True)