#include <chrono>
#include <ctime>
#include <fstream>
#include <future>
#include <iostream>
#include <memory>
#include <sstream>
#include <string>
#include <utility>

#include "translator/parser.h"
#include "translator/response.h"
#include "translator/response_options.h"
#include "translator/service.h"

namespace {

long status_kib(const std::string& key) {
  std::ifstream status("/proc/self/status");
  std::string line;
  std::string label;
  long value = -1;
  while (std::getline(status, line)) {
    std::istringstream row(line);
    row >> label >> value;
    if (label == key + ":")
      return value;
  }
  return value;
}

long mem_available_kib() {
  std::ifstream meminfo("/proc/meminfo");
  std::string label;
  long value = -1;
  std::string unit;
  while (meminfo >> label >> value >> unit) {
    if (label == "MemAvailable:")
      return value;
  }
  return value;
}

}  // namespace

int main(int argc, char* argv[]) {
  using namespace marian::bergamot;
  ConfigParser<AsyncService> parser("Bergamot warm benchmark", false);
  parser.parseArgs(argc, argv);
  auto& config = parser.getConfig();
  AsyncService service(config.serviceConfig);

  const auto load_start = std::chrono::steady_clock::now();
  auto options = parseOptionsFromFilePath(config.modelConfigPaths.front());
  auto model = service.createCompatibleModel(options);
  const auto load_ms = std::chrono::duration<double, std::milli>(
      std::chrono::steady_clock::now() - load_start).count();
  std::cerr << "model_load_ms=" << load_ms << '\n';

  ResponseOptions response_options;
  std::string input;
  unsigned request = 0;
  double measured_ms = 0.0;
  std::clock_t cpu_start = 0;
  while (std::getline(std::cin, input)) {
    if (input.empty())
      continue;
    std::promise<Response> promise;
    auto result = promise.get_future();
    const auto start = std::chrono::steady_clock::now();
    if (request == 1)
      cpu_start = std::clock();
    service.translate(model, std::move(input),
                      [&promise](Response&& response) {
                        promise.set_value(std::move(response));
                      }, response_options);
    auto response = result.get();
    const auto elapsed = std::chrono::duration<double, std::milli>(
        std::chrono::steady_clock::now() - start).count();
    if (request > 0)
      measured_ms += elapsed;
    std::cout << request << '\t' << elapsed << '\t'
              << response.target.text << '\n';
    ++request;
  }
  const double cpu_s = static_cast<double>(std::clock() - cpu_start) / CLOCKS_PER_SEC;
  std::cerr << "measured_requests=" << (request > 0 ? request - 1 : 0)
            << " measured_cpu_s=" << cpu_s
            << " measured_wall_s=" << measured_ms / 1000.0
            << " cpu_one_core_percent="
            << (measured_ms > 0 ? cpu_s * 100000.0 / measured_ms : 0.0)
            << " vmhwm_kib=" << status_kib("VmHWM")
            << " mem_available_kib=" << mem_available_kib() << '\n';
}
