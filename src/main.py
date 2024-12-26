import pprint
import pandas as pd

from parser import RealtyParser


def main():
    data = RealtyParser().start_parce()

    # pprint.pprint(data)

    df = pd.DataFrame(data)
    df.to_excel('output.xlsx', index=False)


if __name__ == '__main__':
    main()
