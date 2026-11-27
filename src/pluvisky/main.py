from pluvisky.services.bmkg_service import BmkgService

def main() -> None:
    bmkg_service = BmkgService()
    results = bmkg_service.get_data_forecast("31.71.01.1002") # testing 
    print(results)

if __name__ == "__main__": 
    main()