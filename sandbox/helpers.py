def convert_str_to_float(s):
    try:
        f = float(s.replace(',','')
            .replace('$','')
            .replace('\n','')
            .replace('*','')
            .replace('?','')
            .replace('-',''))
    except:
        f = .0
        
    return f
        