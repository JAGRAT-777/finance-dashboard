import os
import json
from flask import Flask, render_template, request, session, redirect, url_for, flash
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure the Gemini API key
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Create a Flask web application
app = Flask(__name__)
app.secret_key = 'your_super_secret_key_here' # Change this to a random string

# Function to load financial data from the JSON file
def load_financial_data():
    with open('data.json', 'r') as f:
        return json.load(f)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == 'user' and request.form['password'] == 'pass':
            session['logged_in'] = True
            flash('You were successfully logged in!')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials. Please try again.')
    return render_template('login.html')

@app.route('/')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    financial_data = load_financial_data()
    total_assets = sum(financial_data['assets'].values())
    
    return render_template(
        'dashboard.html', 
        assets=financial_data['assets'],
        total_assets=total_assets,
        liabilities=financial_data['liabilities'],
        credit_score=financial_data['credit_score']
    )

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json['message']
    permissions = request.json.get('permissions', [])
    all_data = load_financial_data()
    allowed_data = {key: all_data[key] for key in permissions if key in all_data}

    prompt = f"""
    You are a helpful and friendly personal finance assistant. 
    Your goal is to provide clear, actionable insights based ONLY on the financial data provided to you.
    After your answer, add a special marker `---SUGGESTIONS---`.
    After the marker, provide exactly three relevant follow-up questions the user might ask next. Each suggestion must be on a new line.

    Here is the user's financial data you are allowed to see:
    ---
    {json.dumps(allowed_data, indent=2)}
    ---
    The user's question is: "{user_message}"
    """
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        response = model.generate_content(prompt)
        raw_text = response.text
        parts = raw_text.split('---SUGGESTIONS---')
        ai_reply = parts[0].strip().replace('\n', '<br>')
        suggestions = [s.strip() for s in parts[1].strip().split('\n')] if len(parts) > 1 else []
        return {'reply': ai_reply, 'suggestions': suggestions}
    except Exception as e:
        print(f"❌ AN ERROR OCCURRED: {e}")
        return {'reply': 'Sorry, an error occurred on the server.'}

@app.route('/transactions')
def transactions():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    # Load the financial data
    financial_data = load_financial_data()
    # Pass the list of transactions to the HTML file
    return render_template('transactions.html', transactions=financial_data['transactions'])

@app.route('/portfolio')
def portfolio():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    financial_data = load_financial_data()
    # Pass the investments data to the portfolio page
    return render_template('portfolio.html', investments=financial_data['assets']['investments'])

@app.route('/epf_credit')
def epf_credit():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    financial_data = load_financial_data()
    # Pass EPF and credit score data
    return render_template('epf_credit.html', 
                           epf_balance=financial_data['epf_balance'], 
                           credit_score=financial_data['credit_score'])

@app.route('/assets_liabilities')
def assets_liabilities():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    financial_data = load_financial_data()
    # Pass the full assets and liabilities dictionaries
    return render_template('assets_liabilities.html', 
                           assets=financial_data['assets'], 
                           liabilities=financial_data['liabilities'])

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out.')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)