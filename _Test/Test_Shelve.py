def Save_Variables(filename='tmp',globals_=None):
    if globals_ is None:
        globals_ = globals()

    globals()
    import shelve
    my_shelf = shelve.open('Saved_Variables.dat', 'n')
    for key, value in globals_.items():
        if not key.startswith('__'):
            try:
                my_shelf[key] = value
            except Exception:
                print('ERROR shelving: "%s"' % key)
            else:
                print('shelved: "%s"' % key)
    my_shelf.close()
    
    
def Load_Variables(filename='Saved_Variables.dat',globals_=None):
    import shelve
    my_shelf = shelve.open(filename)
    for key in my_shelf:
        globals()[key]=my_shelf[key]
    my_shelf.close()