import numpy as np

def find_and_set_categoricals(df):
    '''
    Experimental utility to find undefined categorical categories
    '''

    categorical_fields = []
    non_categorical_object_fields = []

    for c in df.columns:

        print(c)

        if df[c].values.dtype == 'object':

            if len(df) > 3000 and len(np.unique(df[c].head(3000).astype('str'))) <= 128:
                df[c] = df[c].astype('category')
                categorical_fields.append(c)

            elif len(df) > 1000 and len(np.unique(df[c].head(1000).astype('str'))) <= 128:
                df[c] = df[c].astype('category')
                categorical_fields.append(c)

            elif len(np.unique(df[c].astype(str))) <= 128:
                df[c] = df[c].astype('category')
                categorical_fields.append(c)

            else:
                non_categorical_object_fields.append(c)

        elif 'int' in str(df[c].values.dtype):

            if len(df) > 100 and len(np.unique(df[c])) < 20:
                df[c] = df[c].astype('category')
                categorical_fields.append(c)

    return categorical_fields, non_categorical_object_fields
