from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/test', methods=['GET'])
def test_form():
    return '''
    <form action="/submit" method="POST">
        <select name="calendar">
            <option value="work">Work</option>
            <option value="todo">TODO</option>
        </select>
        <button type="submit">Submit</button>
    </form>
    '''

@app.route('/submit', methods=['POST'])
def submit():
    calendar_type = request.form.get('calendar')
    return jsonify({'calendar_type': calendar_type})

if __name__ == '__main__':
    app.run(debug=True)
