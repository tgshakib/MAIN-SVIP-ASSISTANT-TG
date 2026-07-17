from flask import Flask, send_file
app = Flask(__name__)

@app.route('/')
def download():
    return send_file(
        'mybot_backup.zip',
        as_attachment=True,
        download_name='mybot_backup.zip'
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
