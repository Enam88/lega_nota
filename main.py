from functions import clean_marque_verbal, clean_marque_visuelle, wsdl_connect,commmerce_name_search
#from test import domain_name_checker
import pdfkit
# import concurrent.futures 
# import threading



from flask import Flask, render_template, request, Response, redirect
from datetime import datetime
# import time


#display trademark logo in dataframe and convert to html
def to_img_tag(path):
    return '<img src="'+  (path) + '" width="80"  >'



app = Flask(__name__)
# @app.route("/home", methods=['POST', 'GET'])
# def home():
#     return render_template('page.html')

@app.route("/home")
def home():
    # query = request.form["term_searched"]
    return render_template('page.html')




@app.route("/handle_data", methods=['POST', 'GET'])
def handle_data():
    now = datetime.now() # current date and time
    date_time = now.strftime("%d/%m/%Y")
    if request.method == 'POST':

        query = request.form["term_searched"]
    # return query
    xml = wsdl_connect(query)
    with open('lega.xml', 'w') as f:
        f.write(xml)
    df_verbal = clean_marque_verbal('lega.xml')
    df_visuelle = clean_marque_visuelle('lega.xml')
    #df_domain = domain_name_checker(query)
    df_commerce = commmerce_name_search(query)

    
    # Get the HTML output
    out =  render_template('index.html', datetime = str(date_time), marque=query.capitalize(),
                            tables=[df_verbal.to_html(index=False), df_visuelle.to_html(index=False, escape=False,formatters=dict(Logo=to_img_tag)), 
                            df_commerce.to_html(index=False)], titles=['na','1.1 Marque Suisse (verbale)' , '1.2 Marque Suisse (logo)', '1.3 Registre du commerce suisse','1.4 Noms de domaine'])#, df_domain.to_html(index=False)], 
                            # titles=['na','1.1 Marque Suisse (verbale)' , '1.2 Marque Suisse (logo)', '1.3 Registre du commerce suisse','1.4 Noms de domaine'])

    #PDF options
    options = {
        "orientation": "portrait",
        "page-size": "A4",
        "margin-top": "1.0cm",
        "margin-right": "1.0cm",
        "margin-bottom": "1.0cm",
        "margin-left": "1.0cm",
        "encoding": "UTF-8",
        'enable-local-file-access': None,
        '--allow': ''        
        
    }

#     # Build PDF from HTML 
    config = pdfkit.configuration(wkhtmltopdf='C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe')
    pdf = pdfkit.from_string(out, configuration=config, options=options)#, css=css)#{"--allow": ""}) #, options={"enable-local-file-access": ""}, configuration=config)

    # Download the PDF
    # threading.Thread(target=domain_name_checker, args=query ).start()

    return Response(pdf, mimetype="application/pdf")

    
    



if __name__ == '__main__':
    app.run(debug=True)#, host='0.0.0.0')

