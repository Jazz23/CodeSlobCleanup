import verbose_script

def main():
    print("Running LLOC Tests...")
    
    data = {"header": "H1", "body": "B1", "footer": "F1"}
    result = verbose_script.monolithic_processor(data)
    print("Monolithic Processor Result:", result)
    
    print("LLOC Tests Finished.")

if __name__ == "__main__":
    main()
