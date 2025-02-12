import sys
path = '/home/yourusername/mysite'  # Kullanıcı adınızla değiştirin
if path not in sys.path:
    sys.path.append(path)

# Her iki uygulamayı da import et
from remove import app as remove_app
from text_to_speech import app as tts_app

# URL prefix'lerine göre yönlendirme yap
class PrefixMiddleware(object):
    def __init__(self, app, prefix=''):
        self.app = app
        self.prefix = prefix

    def __call__(self, environ, start_response):
        if environ['PATH_INFO'].startswith(self.prefix):
            environ['PATH_INFO'] = environ['PATH_INFO'][len(self.prefix):]
            environ['SCRIPT_NAME'] = self.prefix
            return self.app(environ, start_response)
        return self.app(environ, start_response)

# Ana uygulama
application = PrefixMiddleware(remove_app, '/remove')
application = PrefixMiddleware(tts_app, '/tts')

if __name__ == '__main__':
    application.run() 