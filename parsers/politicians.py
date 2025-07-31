import json
import datetime
def overlaps(service_start, service_end, parliament_start, parliament_end):
    return service_start < parliament_end and parliament_start < service_end

def extract_party(service):
            raw_party = [x for x in service['SecondaryService'] if x['RoSType'] == 'Parties Represented']
            party= raw_party[0]['Value'] if len(raw_party) else None
            return party

def parse_dates(data, start_key, end_key):
    parsed = []
    for d in data:
        start_str = d.get(start_key, "")
        end_str = d.get(end_key, "")
        try:
            start = datetime.datetime.strptime(start_str, "%Y-%m-%d")
            end = datetime.datetime.strptime(end_str, "%Y-%m-%d")
            parsed.append((start, end, d))
        except (ValueError, TypeError):
            start = datetime.datetime.strptime(start_str, "%Y-%m-%d")
            end = datetime.datetime(2099,1,1)
            parsed.append((start, end, d))
    return parsed

with open("scrapers/raw_sources/politicians.json", "r") as f:
    data  = json.load(f)
with open("scrapers/raw_sources/parliaments.json", "r") as f:
    parliaments = json.load(f)['value']
    parliament_intervals = parse_dates(parliaments, "DateElection", "ParliamentEnd")

for politician in data['value']:
    format_dict = {
            'firstName': politician['PreferredName'][1:-1] if politician['PreferredName'] else politician['GivenName'],
            'lastName':politician['FamilyName'],
            'firstNations':politician['FirstNations'],
            'image':politician['Image'],
            'gender':politician['Gender'],
            # 'dob':datetime.datetime.strptime(politician['DateOfBirth'],"%Y-%m-%d")
            }
    isSenate = politician['SenateState'] != ''
    if isSenate:
        services = []
        raw_services = politician['PartyParliamentaryService']
        for service in raw_services:
            # Stupid exception
            try:
                service_start = datetime.datetime.strptime(service['DateStart'], "%Y-%m-%d")
            except ValueError:
                print(service['DateStart'])
                service_start = datetime.datetime.strptime(f"{service['DateStart'][:-1]}{int(service['DateStart'][-1]) - 1}", "%Y-%m-%d")

            service_end_str = service.get('DateEnd')
            try:
                service_end = datetime.datetime.strptime(service_end_str, "%Y-%m-%d") if service_end_str else datetime.datetime(2099, 1, 1)
            except ValueError:
                service_end = datetime.datetime.strptime(f"{service_end_str[:-1]}{int(service_end_str[-1]) - 1}", "%Y-%m-%d")

            matching_parliaments = [
                d["PID"] for s, e, d in parliament_intervals
                if overlaps(service_start, service_end, s, e)
                    ]
            services.append({
                'party':extract_party(service),
                'startDate':service['DateStart'], 
                'endDate': service['DateEnd'],
                'isSenate': isSenate,
                'seat': None,
                'state': politician['SenateState'],
                'parliament': matching_parliaments
                })

    else:
        raw_party_service = [{
            'party': extract_party(x),
            'startDate': x['DateStart'],
            'endDate': x['DateEnd']
            } for x in politician['PartyParliamentaryService']]
        raw_seat_service =  politician['ElectorateService']
        
        seat_intervals = parse_dates(raw_seat_service, "ServiceStart", "ServiceEnd")
        party_intervals = parse_dates(raw_party_service, "startDate", "endDate")

        # Get all unique date boundaries
        all_dates = set()
        for start, end, _ in seat_intervals + party_intervals + parliament_intervals:
            all_dates.update([start, end])
        sorted_dates = sorted(all_dates)

        # Create atomic intervals from consecutive dates
        atomic_intervals = [(sorted_dates[i], sorted_dates[i+1]) for i in range(len(sorted_dates)-1)]

        # For each atomic interval, find matching seat, party, and parliament
        services = []
        for start, end in atomic_intervals:
            seat = next((d for s, e, d in seat_intervals if s <= start < e), None)
            party = next((d for s, e, d in party_intervals if s <= start < e), None)
            parliament = next((d for s, e, d in parliament_intervals if s <= start < e), None)
            
            if seat and party and parliament:
                services.append({
                    "ServiceStart": start.strftime("%Y-%m-%d"),
                    "ServiceEnd": end.strftime("%Y-%m-%d"),
                    "Electorate": seat["Electorate"],
                    "State": seat["State"],
                    "party": party["party"],
                    "Parliament": [parliament["PID"]]
                })

    #print(services)

        # `results` now contains the unified service periods





        


        







