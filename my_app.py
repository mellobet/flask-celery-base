from time import sleep

from flask import Flask
from flask import render_template

import tasks

flask_app = Flask(__name__)
flask_app.config.update(
    broker_url='redis://redis:6379/0',
    result_backend='redis://redis:6379/0'
)

celery = tasks.make_celery(flask_app)

@celery.task()
def add_together(a, b):
    sleep(15)
    return str(a + b)


@flask_app.route('/submit')
def test():
    submit_task = add_together.delay(1, 2)
    
    ctx = {
        't_id': submit_task.id
    }
    return render_template('submit.html', ctx=ctx)

@flask_app.route('/task-status/<uuid:task_id>')
def task_status(task_id):
    result = celery.AsyncResult(str(task_id))

    ctx = {
        't_id': task_id,
        'state': result.state
    }

    return render_template('live_status.html', ctx=ctx)


@flask_app.route('/inspect')
def celery_inspect():
    i = celery.control.inspect()
    workers = [k for k in i.active().keys()]
    workers_data = {}
    for worker in workers:
        data = {
            'active': len(i.active()[worker]),
            'reserved': len(i.reserved()[worker]),
            'scheduled': len(i.scheduled()[worker]),
            'registered': len(i.registered()[worker]),
        }
        workers_data.update({worker: data})
    ctx = {
        'data': workers_data
    } 
    return render_template('inspect.html', ctx=ctx)
