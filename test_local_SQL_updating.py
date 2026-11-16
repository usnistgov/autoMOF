import pandas as pd
from pandas.core.indexing import _iLocIndexer, _LocIndexer 

class test_dict(dict):
    def __setitem__(self, key, value):
        print("Hello")
        return dict.__setitem__(self, key, value)

class CustomLocIndexer(_LocIndexer):
    def __setitem__(self, key, value):
        # key can be a tuple like (row, col) or a single row indexer
        if isinstance(key, tuple) and len(key) >= 2:
            row_key, col_key = key[0], key[1]
            print(f"Updating column: '{col_key}' with value: '{value}'")
        else:
            print(f"Updating with key: '{key}' and value: '{value}'")
       
        # Call the original __setitem__ of _LocIndexer to apply the update
        super().__setitem__(key, value)


class CustomiLocIndexer(_iLocIndexer):
    def __setitem__(self, key, value):
        if isinstance(key, tuple) and len(key) >= 2:
            row_idx, col_idx = key[0], key[1]
            # Get the column name from the integer index
            col_name = self.obj.columns[col_idx]
            print(f"Updating column: '{col_name}' (index: {col_idx}) with value: '{value}'")
        else:
            print(f"Updating with key: '{key}' and value: '{value}'")
        super().__setitem__(key, value)


class CustomDataFrame(pd.DataFrame):
    _metadata = []
 
    def __setitem__(self, idx, value):
        print("Woo")
        print("Index: ", idx)
        print("Value: ", value)
        return super().__setitem__(idx, value)
 
    @property
    def _constructor(self):
        return CustomDataFrame
    
    @property
    def loc(self):
        return CustomLocIndexer("loc", self)

    @property
    def iloc(self):
        return CustomiLocIndexer("iloc", self)
 

# class test_iloc(_iLocIndexer):
#     def __setitem__(self, key, value):
#         print("Class-seption")
#         return super().__setitem__(key, value)

# class test_df(pd.DataFrame):
#     def __init__(self):
#         super().__init__()
#         # self.iloc = test_iloc

#     def __setitem__(self, idx, value):
#         print("Woo")
#         print("Index: ", idx)
#         print("Value: ", value)
#         return super().__setitem__(idx, value)

#     @property
#     def loc(self):
#         print("Loc")
#         print("Loc index: ", self.index)
#         return super().loc

#     @property
#     def iloc(self):
#         print("Iloc")
#         return test_iloc("iloc", self)



def main():
    dictionary = test_dict()
    dictionary["Hello"] = "There"
    print(dictionary)
    dataframe = CustomDataFrame()

    # dataframe = test_df()
    dataframe["Does this"] = ["Work", "Or something"]
    print(dataframe)
    dataframe.loc[1, "Does this"] = "A thing"
    print(dataframe)

if __name__ == "__main__":
    main()