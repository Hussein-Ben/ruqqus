from ruqqus.helpers.wrappers import *
from flask import *
from ruqqus.__main__ import app

#Errors
@app.errorhandler(401)
@auth_desired
def error_401(e, v):
    return render_template('errors/401.html', v=v), 401

@app.errorhandler(403)
@auth_desired
def error_403(e, v):
    return render_template('errors/403.html', v=v), 403

@app.errorhandler(404)
@auth_desired
def error_404(e, v):
    return render_template('errors/404.html', v=v), 404

@app.errorhandler(405)
@auth_desired
def error_405(e, v):
    return render_template('errors/405.html', v=v), 405

@app.errorhandler(409)
@auth_desired
def error_409(e, v):
    return render_template('errors/409.html', v=v), 409

@app.errorhandler(413)
@auth_desired
def error_413(e, v):
    return render_template('errors/413.html', v=v), 413

@app.errorhandler(422)
@auth_desired
def error_422(e, v):
    return render_template('errors/422.html', v=v), 422

@app.errorhandler(429)
@auth_desired
def error_429(e, v):
    return render_template('errors/429.html', v=v), 429

@app.errorhandler(451)
@auth_desired
def error_451(e, v):
    return render_template('errors/451.html', v=v), 451

@app.errorhandler(500)
@auth_desired
def error_500(e, v):
    return render_template('errors/500.html', e=e, v=v), 500
