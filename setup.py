from setuptools import setup, find_packages, findall

setup(name             = 'calandigital',
      version          = '0.1',
      description      = 'Helper package to ease the development of CASPER\'s ROACH1 and ROACH2 scripts.',
      url              = 'http://github.com/francocalan/calandigital',
      author           = 'Franco Curotto',
      author_email     = 'francocurotto@gmail.com',
      license          = 'GPL v3',
      packages         = ['calandigital'],
      scripts          = findall('scripts/'),
      install_requires = [line.rstrip('\n') for line in open('REQUIREMENTS') if not line.startswith('git+https://')],
      dependency_links = [line.rstrip('\n') for line in open('REQUIREMENTS') if line.startswith('git+https://')],
      zip_safe         = False)
