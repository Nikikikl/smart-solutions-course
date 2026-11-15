"""Compile actual normal firmware persistence with an atomic, synthetic NVS fake.

Only SDK/String/Preferences declarations are replaced. No device or network IO.
Power-loss injection throws after one committed NVS operation, between calls.
"""
from pathlib import Path
import shutil
import subprocess

import pytest

FW = Path(__file__).resolve().parents[1] / "firmware"

ARDUINO = r'''
#pragma once
#include <string>
#include <cstdint>
#include <initializer_list>
class String : public std::string {
 public:
  using std::string::string;
  String(const std::string& s):std::string(s){}
  bool isEmpty() const {return empty();}
};
'''
PREFERENCES = r'''
#pragma once
#include "Arduino.h"
#include <map>
#include <functional>
struct PowerLoss {};
class Preferences {
 public:
  inline static std::map<std::string,std::string> data;
  inline static int operations=0,failAt=0,cutAt=0;
  inline static bool beginOk=true;
  inline static int missingStrings=0;
  inline static std::function<void(const char*)> afterWrite;
  static void faults(int failure=0,int cut=0){operations=0;failAt=failure;cutAt=cut;}
  bool begin(const char*,bool){return beginOk;}
  bool isKey(const char* k){return data.count(k);}
  String getString(const char* k,const char* fallback){
    if(!data.count(k))++missingStrings;
    return data.count(k)?data[k]:fallback;
  }
  bool getBool(const char* k,bool fallback){return data.count(k)?data[k]=="true":fallback;}
  bool mutate(const char* k,const std::string& v,bool erase=false){
    ++operations;
    if(operations==failAt)return false;
    if(erase)data.erase(k);else data[k]=v;
    if(operations==cutAt)throw PowerLoss{};
    if(afterWrite)afterWrite(k);
    return true;
  }
  size_t putString(const char* k,const String& v){return mutate(k,v)?v.length():0;}
  size_t putBool(const char* k,bool v){return mutate(k,v?"true":"false")?sizeof(bool):0;}
  bool remove(const char* k){return mutate(k,"",true);}
};
'''
PROGRAM = r'''
#include "persistent_state.h"
#include <cassert>
#include <cstdlib>
#include <string>
#include <future>
#include <chrono>
using postoffice::PersistentState;
void reset(){Preferences::data.clear();Preferences::faults();Preferences::beginOk=true;
  Preferences::missingStrings=0;Preferences::afterWrite=nullptr;}
void claimed(PersistentState& s){assert(s.begin());assert(s.startClaim("job-1"));Preferences::faults();}
void terminal(PersistentState& s){claimed(s);assert(s.queueRefused("job-1","station_refused"));Preferences::faults();}
int main(int argc,char**argv){
  reset();std::string mode=argv[1];int n=argc>2?atoi(argv[2]):0;
  if(mode=="write"){
    PersistentState s;claimed(s);Preferences::faults(n);
    assert(!s.queueRefused("job-1","station_refused"));assert(!s.healthy());assert(!s.canPoll());
    assert(Preferences::data["activeId"]=="job-1");assert(Preferences::data["resultReady"]!="true");
    Preferences::faults();PersistentState reboot;assert(reboot.begin());assert(!reboot.canPoll());
    assert(reboot.pendingResult().status=="refused");
  }else if(mode=="cut-terminal"){
    PersistentState s;claimed(s);Preferences::faults(0,n);
    try{s.queueDone("job-1");assert(false);}catch(PowerLoss&){}
    Preferences::faults();PersistentState reboot;assert(reboot.begin());assert(!reboot.canPoll());
    assert(reboot.pendingResult().status==(n==3?"done":"refused"));
    PersistentState secondReboot;assert(secondReboot.begin());assert(!secondReboot.canPoll());
    assert(secondReboot.pendingResult().status==reboot.pendingResult().status);
    assert(!secondReboot.startClaim("job-1"));
  }else if(mode=="ack-fail" || mode=="cut-ack"){
    PersistentState s;terminal(s);Preferences::faults(mode=="ack-fail"?n:0,mode=="cut-ack"?n:0);
    if(mode=="ack-fail"){assert(!s.acknowledgeResult("job-1"));assert(!s.healthy());assert(!s.canPoll());}
    else{try{s.acknowledgeResult("job-1");assert(false);}catch(PowerLoss&) {}}
    Preferences::faults();PersistentState reboot;assert(reboot.begin());
    if(mode=="ack-fail" && n==1){assert(!reboot.canPoll());assert(reboot.pendingResult().jobId=="job-1");}
    else{assert(reboot.canPoll());assert(!reboot.pendingResult().present);}
    PersistentState secondReboot;assert(secondReboot.begin());
    assert(secondReboot.canPoll()==reboot.canPoll());
  }else if(mode=="reason-delete"){
    PersistentState s;claimed(s);Preferences::data["resultReason"]="old";Preferences::faults(3);
    assert(!s.queueDone("job-1"));assert(!s.healthy());assert(Preferences::data["resultReady"]!="true");
  }else if(mode=="legacy"){
    Preferences::data={{"resultReady","true"},{"resultId","job-1"},{"resultStatus","done"}};
    PersistentState s;assert(s.begin());assert(!s.canPoll());assert(s.pendingResult().status=="done");
    assert(s.acknowledgeResult("job-1"));assert(s.canPoll());
  }else if(mode=="corrupt"){
    Preferences::data={{"resultReady","true"},{"resultId","job-1"}};
    PersistentState s;assert(!s.begin());assert(!s.canPoll());assert(!s.queueDone("job-1"));
  }else if(mode=="orphan"){
    Preferences::data={{"resultId","job-1"}};PersistentState s;assert(!s.begin());assert(!s.canPoll());
  }else if(mode=="open-fail"){
    Preferences::beginOk=false;PersistentState s;assert(!s.begin());assert(!s.startClaim("job-1"));
  }else if(mode=="claim-fail"){
    PersistentState s;assert(s.begin());Preferences::faults(1);assert(!s.startClaim("job-1"));assert(!s.canPoll());
  }else if(mode=="wrong-ack"){
    PersistentState s;terminal(s);assert(!s.acknowledgeResult("wrong"));
    assert(Preferences::operations==0);assert(s.pendingResult().jobId=="job-1");
  }else if(mode=="late-done" || mode=="late-refused"){
    PersistentState s;terminal(s);assert(s.acknowledgeResult("job-1"));Preferences::faults();
    assert(!(mode=="late-done"?s.queueDone("job-1"):s.queueRefused("job-1","late")));
    assert(s.canPoll());assert(!s.pendingResult().present);assert(Preferences::operations==0);
  }else if(mode=="concurrent-done" || mode=="concurrent-refused"){
    PersistentState s;terminal(s);
    std::future<bool> late;std::promise<void> entered;auto started=entered.get_future();
    bool once=false;
    Preferences::afterWrite=[&](const char* key){
      if(std::string(key)!="resultReady" || Preferences::data[key]!="false" || once)return;
      once=true;
      late=std::async(std::launch::async,[&]{
        entered.set_value();
        return mode=="concurrent-done"?s.queueDone("job-1"):s.queueRefused("job-1","late");
      });
      started.wait();
      // The other core must wait for the entire acknowledged cleanup.
      assert(late.wait_for(std::chrono::milliseconds(50))==std::future_status::timeout);
    };
    assert(s.acknowledgeResult("job-1"));Preferences::afterWrite=nullptr;
    assert(once);assert(!late.get());assert(s.canPoll());assert(!s.pendingResult().present);
  }else if(mode=="ack-mismatch"){
    Preferences::data={{"ackedId","other"},{"resultReady","true"},
      {"resultId","job-1"},{"resultStatus","done"}};
    const auto before=Preferences::data;PersistentState s;
    assert(!s.begin());assert(!s.canPoll());assert(Preferences::data==before);
  }else if(mode=="optional-reason"){
    PersistentState s;claimed(s);assert(s.queueDone("job-1"));
    for(int i=0;i<100;++i){assert(s.pendingResult().status=="done");assert(!s.canPoll());}
    assert(Preferences::missingStrings==0);
  }else if(mode=="duplicate-terminal"){
    PersistentState s;claimed(s);assert(s.queueDone("job-1"));Preferences::faults();
    assert(s.queueDone("job-1"));assert(!s.queueRefused("job-1","different"));
    assert(!s.startClaim("job-1"));assert(Preferences::operations==0);
    PersistentState reboot;assert(reboot.begin());assert(reboot.pendingResult().status=="done");
  }else return 2;
}
'''


@pytest.fixture(scope="module")
def persistence(tmp_path_factory):
    folder = tmp_path_factory.mktemp("normal-nvs")
    (folder / "Arduino.h").write_text(ARDUINO)
    (folder / "Preferences.h").write_text(PREFERENCES)
    (folder / "test.cpp").write_text(PROGRAM)
    binary = folder / "persistence"
    subprocess.run([shutil.which("c++"), "-std=c++17", "-I", str(folder), "-I", str(FW / "include"),
                    str(FW / "src/persistent_state.cpp"), str(folder / "test.cpp"), "-o", str(binary)],
                   check=True, capture_output=True)
    return binary


@pytest.mark.parametrize("field", range(1, 5), ids=["resultId", "resultStatus", "resultReason", "resultReady"])
def test_failed_terminal_field_never_publishes(persistence, field):
    subprocess.run([str(persistence), "write", str(field)], check=True)


@pytest.mark.parametrize("cut", range(1, 4))
def test_reboot_at_each_terminal_commit(persistence, cut):
    subprocess.run([str(persistence), "cut-terminal", str(cut)], check=True)


@pytest.mark.parametrize("step", range(1, 8), ids=["ackedId", "ready-false", "id-delete", "status-delete", "reason-delete", "active-delete", "ack-delete"])
@pytest.mark.parametrize("mode", ["ack-fail", "cut-ack"])
def test_delivery_cleanup_failures_and_interruptions(persistence, step, mode):
    subprocess.run([str(persistence), mode, str(step)], check=True)


@pytest.mark.parametrize("mode", ["reason-delete", "legacy", "corrupt", "orphan", "open-fail", "claim-fail", "wrong-ack"])
def test_legacy_and_fail_closed_states(persistence, mode):
    subprocess.run([str(persistence), mode], check=True)


@pytest.mark.parametrize("mode", ["late-done", "late-refused", "concurrent-done", "concurrent-refused",
                                  "ack-mismatch", "optional-reason", "duplicate-terminal"])
def test_review_regressions(persistence, mode):
    subprocess.run([str(persistence), mode], check=True, timeout=10)


def test_normal_http_uses_verified_connect_and_sntp_gate():
    source = (FW / "src/post_office_client.cpp").read_text()
    assert "int connect(const char* host,uint16_t port,int32_t timeout) override" in source
    assert "sntp_set_time_sync_notification_cb(timeSynchronized)" in source
    assert "std::atomic<bool> utcSynchronized{false}" in source
    assert "mbedtls_x509_crt_verify" in source
    assert source.count("ValidityCheckedClient client(rootCa_)") == 2
    assert "setInsecure(" not in source
    assert 'if (!state_->healthy())' in source


def test_sensor_confirmation_is_ram_only_and_on_existing_page():
    source = (FW / "src/main.cpp").read_text()
    page = (FW / "include/web_page.h").read_text()
    assert "bool pressureSensorConfirmed = false" in source
    assert "pressure::convertSensorReading(readPressureRawAdc(), pressureCalibration, pressureSensorConfirmed)" in source
    assert 'webServer.arg("sensor_confirmed")' in source
    assert 'id="sensorConfirmed"' in page
    assert "f.set('sensor_confirmed',sensorConfirmed.checked?'1':'0')" in page
    store = (FW / "src/pressure_settings.cpp").read_text()
    assert "sensor_confirmed" not in store and "pressureSensorConfirmed" not in store


def test_atom_page_server_test_shows_server_answer_and_pressure_defaults():
    source = (FW / "src/main.cpp").read_text()
    page = (FW / "include/web_page.h").read_text()
    store = (FW / "src/pressure_settings.cpp").read_text()
    assert "postOfficeClient.testConnection(&httpStatus, &serverResponse)" in source
    assert 'document["server_response"] = excerpt;' in source
    assert "p.server_response" in page
    assert "if (!hasStoredCalibration()) return dataAcquisitionLab2Calibration();" in store
    assert 'document["defaults"]' in source
    assert "fillPressureDefaults()" in page
    # Still one page: no new HTML route was added.
    assert source.count("LAB2_INDEX_HTML") == 1
