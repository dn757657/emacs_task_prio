from PyOrgMode.PyOrgMode import PyOrgMode


def main():
    orgts = "<2006-11-01 Wed 19:15>"
    tdate = PyOrgMode.OrgDate(orgts)
    print()


if __name__ == '__main__':
    main()